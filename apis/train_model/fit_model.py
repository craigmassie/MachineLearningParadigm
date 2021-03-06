from threading import Thread
import os
import logging
import json
import io
import numpy as np

class FitModelFromGenerators(Thread):
    """
    Thread to train a given model, from train and test generators that flow from directory. Model and its metric later saved to disk.
    """
    def __init__(self, request, model, train_gen, test_gen, unique_id, model_location, epochs = 5):
        Thread.__init__(self)
        self.request = request
        self.model = model
        self.train_gen = train_gen
        self.test_gen = test_gen
        self.unique_id = str(unique_id)
        self.model_location = model_location
        self.epochs = epochs
        self.logger = logging.getLogger(__name__)

    def _save_model_performance_metrics(self, evaluate_generator, model_dir, history):
        to_unicode = str
        score = {"Test Loss": to_unicode(evaluate_generator[0]), "Test accuracy" : to_unicode(evaluate_generator[1])}
        #Save final score
        self.logger.info("Attempting to save model score.")
        with io.open(os.path.join(model_dir, "final_score.json"), 'w') as outfile:
            json_output = json.dumps(score,
                            indent=4, sort_keys=True,
                            separators=(',', ': '), ensure_ascii=False)
            outfile.write(to_unicode(json_output))
        formatted_history = {}
        for k in history.history:
            formatted_history[k] = [float(x) for x in history.history[k]]
        #Save history of model training (later used for visualisation)
        self.logger.info("Attempting to save model history.")
        with io.open(os.path.join(model_dir, "history.json"), 'w') as historyfile:
            hist_output = json.dumps(formatted_history,
                            indent=4, sort_keys=True,
                            separators=(',', ': '), ensure_ascii=False)
            historyfile.write(to_unicode(hist_output))

    def _get_arr_from_gen(self, generator):
        x_size = (generator.samples,) + (generator.image_shape)
        y_size = (generator.samples,) + (generator.num_classes,) 
        x_app = np.empty(shape = x_size)
        y_app = []

        batch_index = 0
        batch_size = generator.batch_size
        while batch_index <= generator.batch_index:
            data = generator.next()
            for idx, x in enumerate(data[0]):
                x_app[(idx + (batch_index*batch_size))] = x
            for _, x in enumerate(data[1]):
                y_app.append(x)
            batch_index = batch_index + 1

        return x_app, np.array(y_app)

    def run(self):
        model_dir= os.path.join(os.path.dirname(self.model_location), self.unique_id)
        self.logger.info(model_dir)
        infoTxt = os.path.join(model_dir, 'trainingInfo.txt')
        try:
            os.makedirs(model_dir, exist_ok=True)
            f = open(infoTxt, "w")
            f.write("Training")
            f.close()
        except OSError as e:
            self.logger.error(f"Unable to create directory to save model. {e}")
        self.logger.info("Attempting to fit model.")
        try:
            '''fit_from_generator deprecated, steps_per_epoch required as per issue https://github.com/tensorflow/tensorflow/issues/35422'''
            (x_train, y_train) = self._get_arr_from_gen(self.train_gen)
            (x_test, y_test) = self._get_arr_from_gen(self.test_gen)
            history = self.model.fit(x=x_train, y=y_train, epochs=self.epochs, verbose=1, validation_split=0.2)
            score = self.model.evaluate(x=x_test, y=y_test)
            model_file_name = ''.join([self.unique_id, ".h5"])
            self._save_model_performance_metrics(score, model_dir, history)
            model_save_location = os.path.join(model_dir, model_file_name)
            self.logger.info("Attempting to save model.")
            self.model.save(model_save_location)
            os.remove(infoTxt)
        except Exception as e:
            self.logger.error(f"Failed training process due to: {e}")
            f = open(infoTxt, "w")
            f.write(f"Failed training process due to: {e}")
            f.close()

class FitModelFromTrainTest(Thread):
    """
    TODO: Holding off implementation until training from generators tested on Azure.
    """
    def __init__(self):
        pass