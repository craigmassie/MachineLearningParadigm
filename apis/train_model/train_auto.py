from threading import Thread
import os
import logging
import json
import io
import autokeras as ak
import tensorflow as tf
import numpy as np
import zipfile
import uuid
from tensorflow.keras.callbacks import CSVLogger
import csv

class AutoMLTrain(Thread):
    """
    Thread to train a Auto-Keras model of the type specified by auto_type. 
    Evaluates a ∈ A for number of epochs, where |A| = trials.
    Model and metrics saved to disk at model_location.
    """
    def __init__(self, request, model_location, dataset_location, unique_id, auto_type, logger, epochs=5, trials=10):
        Thread.__init__(self)
        self.request = request
        self.model_location = model_location
        self.dataset_location = dataset_location
        self.unique_id = str(unique_id)
        self.epochs = epochs
        self.trials = trials
        self.auto_type = auto_type
        self.logger = logger

    def _load_dataset_into_gen(self, dataset_location):
        filename = os.path.basename(dataset_location).split('.')[0]
        if(dataset_location.endswith(".zip")):
            extraction_dir = os.path.splitext(dataset_location)[0]
            if (not os.path.isdir(extraction_dir)):
                try:
                    with zipfile.ZipFile(dataset_location,"r") as zip_ref:
                        zip_ref.extractall(path=extraction_dir)
                except Exception as e:
                    print(e)
            dataset_location = os.path.join(extraction_dir, filename)
        training_data_location = os.path.join(dataset_location, "train")
        test_data_location = os.path.join(dataset_location, "test")
        if not os.path.exists(training_data_location):
            print(f"Unable to find training data directory at location {training_data_location}")
            return
        if not os.path.exists(test_data_location):
            print(f"Unable to find training data directory at location {test_data_location}")
            return

        train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(validation_split=0.2)
        train_generator = train_datagen.flow_from_directory(training_data_location,class_mode='sparse', shuffle=True, target_size=(128,128), seed=42)

        test_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
        test_generator = test_datagen.flow_from_directory(test_data_location, class_mode='sparse',target_size=(128,128), shuffle=True, seed=42)
        return train_generator, test_generator

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

    def _create_history_json(self, csv_location, score):
        VAL_ACCURACY_CSV_INDEX = 3
        VAL_LOSS_CSV_INDEX = 4

        with open(csv_location, newline='') as f:
            reader = csv.reader(f)
            data = list(reader)
        accuracy = []
        loss = []
        for row in data[1:]:
            accuracy.append(row[VAL_ACCURACY_CSV_INDEX])
            loss.append(row[VAL_LOSS_CSV_INDEX])

        #Conversions from string to float
        accuracy = [float(x) for x in accuracy]
        loss = [float(x) for x in loss]

        history = {"accuracy" : accuracy, "loss" : loss}
        with io.open(os.path.join(os.path.dirname(csv_location), "history.json"), 'w') as historyfile:
            hist_output = json.dumps(history,
                            indent=4, sort_keys=True,
                            separators=(',', ': '), ensure_ascii=False)
            historyfile.write(str(hist_output))

    def _export_model(self, clf):
        model = clf.export_model()
        file_name = self.unique_id + ".h5"
        model.save(os.path.join(self.model_location, self.unique_id, file_name))

    def run(self):
        if self.auto_type != "ImageClassifier": return
        train_gen, test_gen = self._load_dataset_into_gen(self.dataset_location)
        classification_type = train_gen.num_classes
        class_file_loc = os.path.join(self.model_location, self.unique_id, "classes.npy")
        try:
            if not(os.path.isdir(os.path.dirname(class_file_loc))):
                os.makedirs(os.path.dirname(class_file_loc), exist_ok = True) 
            np.save(class_file_loc, train_gen.class_indices, allow_pickle=True)
        except Exception as e:
            self.logger.info(f"Unable to save class indices. {e}")
        (x_train, y_train) = self._get_arr_from_gen(train_gen)
        (x_test, y_test) = self._get_arr_from_gen(test_gen)
        clf = ak.ImageClassifier(max_trials=self.trials)
        csv_location = os.path.join(self.model_location, self.unique_id, 'log.csv')
        csv_logger = CSVLogger(csv_location, append=True, separator=',')
        clf.fit(x_train, y_train, epochs = self.epochs, callbacks=[csv_logger])
        score = clf.evaluate(x_test, y_test)
        self._create_history_json(csv_location, score)
        self._export_model(clf)
        return(200)
