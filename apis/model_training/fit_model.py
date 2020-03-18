from threading import Thread
import os
import logging

class FitModel(Thread):
    def __init__(self, request, model, train_gen, test_gen, unique_id, model_location, epochs = 5):
        Thread.__init__(self)
        self.request = request
        self.model = model
        self.train_gen = train_gen
        self.test_gen = test_gen
        self.unique_id = unique_id 
        self.model_location = model_location
        self.epochs = epochs
        self.logger = logging.getLogger("model-training")
        self.logger.setLevel(logging.INFO)

    def run(self):
        self.logger.info("Attempting to fit model.")
        self.model.fit_generator(generator=self.train_gen,epochs=self.epochs,verbose=1)
        score = self.model.evaluate_generator(self.test_gen)
        model_file_name = ''.join([self.unique_id, ".h5"])
        model_save_location = os.path.join(self.model_location, self.unique_id, model_file_name)
        self.logger.info("Attempting to save model.")
        self.model.save(model_save_location)
        return('Test loss:', score[0], 'Test accuracy:', score[1])