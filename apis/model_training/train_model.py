from flask import Flask, request, abort
from flask_restful import Resource, Api
import json
import tensorflow as tf
import sys
from tensorflow.keras.datasets import cifar10
import azure_connection
import subprocess
import os
from threading import Thread
import fit_model
import uuid 

app = Flask(__name__)
api = Api(app)
num_classes = 10
epochs = 1
BLOBFUSE_MOUNT_SCRIPT = "/app/mount-blobfuse.sh"

def _request_key_exists(d, request_key):
    try:
        request_value = d[request_key]
    except KeyError:
        app.logger.error(f"'{request_key}' key not found in request body. Unable to find begin training.")
        abort(400)
    return request_value

#Should we even be doing this? Maybe only for FCN?
def _alter_model_input_size(model, new_input_shape):
    model_layers = [l for l in model._layers]
    #Replace input layer with one of correct size
    model_layers[0] = tf.keras.layers.Input(shape=new_input_shape)
    #Ensure output from new layer flows into next layer in model
    model_layers[1] = model_layers[1](model_layers[0])

    curr = model_layers[1]
    #Propogate changes to rest of layers. Not trainable (because transfer learning, and all that jazz).
    for i in range(2, len(model_layers)):
        model_layers[i].trainable = False
        curr = model_layers[i](curr)
        model_layers[i] = curr

    return model_layers

def _add_classifier_to_model(model, num_classes):
    model_layers = model._layers
    for l in model_layers: l.trainable = False
    flatten_layer = tf.keras.layers.Flatten()(model_layers[-1].output)
    classifier = tf.keras.layers.Dense(num_classes, activation='softmax')(flatten_layer)
    model_layers.append(flatten_layer)
    model_layers.append(classifier)
    return tf.keras.Model(model_layers[0].input, model_layers[-1])

def _get_input_dimensions(model):
    model_input = model.layers[0].output
    #Remove shape from Tensor object context (if in one)
    if tf.is_tensor(model_input):
        if hasattr(model_input, 'shape'):
            model_input = model_input.shape
        else:
            app.logger.error("Unable to determine input shape of model.")
            abort(400)
    #Remove tuple from list context (if in one)
    if isinstance(model_input, list):
        if len(model_input) == 1:
            model_input = model_input[0]
    app.logger.info(model_input)
    return model_input[1:3]

def _get_initial_model(model_location):
    return tf.keras.models.load_model(model_location)

def _load_dataset_into_gen(dataset_location, expected_model_input):
    app.logger.info("Attempting to load dataset into generator.")
    training_data_location = os.path.join(dataset_location, "train")
    test_data_location = os.path.join(dataset_location, "test")
    if not os.path.exists(training_data_location):
        app.logger.error(f"Unable to find training data directory at location {training_data_location}")
    if not os.path.exists(test_data_location):
        app.logger.error(f"Unable to find training data directory at location {test_data_location}")

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(validation_split=0.2)
    train_generator = train_datagen.flow_from_directory(training_data_location, target_size=expected_model_input)

    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
    test_generator = test_datagen.flow_from_directory(test_data_location, target_size=expected_model_input)
    return train_generator, test_generator

@app.route('/trainModel', methods=['POST'])
def post():
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    try:
        if os.path.isfile(BLOBFUSE_MOUNT_SCRIPT):
            subprocess.call([BLOBFUSE_MOUNT_SCRIPT], shell=True)
        else:
            raise FileExistsError(f"{BLOBFUSE_MOUNT_SCRIPT} not found.")
    except Exception as e:
        app.logger.error(f"Issue with running blobfuse mounting script {BLOBFUSE_MOUNT_SCRIPT}, please ensure that file exists \
            and that sufficient priveledges are given to all for execution. {e}")
        return(400)

    d = request.get_json()

    #Retrieve info about model and dataset from body
    model_location, dataset_location = _request_key_exists(d, "model_location"), _request_key_exists(d, "dataset_location")

    #Load the model stored at the requested model location
    initial_model = _get_initial_model(model_location)

    #Retrieve the input shape of the initial model
    expected_input_size = _get_input_dimensions(initial_model)

    #Create train and test generators at the dataset location. Processed to expected image shape.
    train_gen, test_gen = _load_dataset_into_gen(dataset_location, expected_input_size)

    #Initialise num_classes to the amount found at directory by generator
    num_classes = len(train_gen.class_indices)

    #Add final layers to the model with num_classes to classify
    transfer_model = _add_classifier_to_model(initial_model, num_classes)

    app.logger.info(f"Model Summary: {transfer_model.summary()}")

    transfer_model.compile(loss='categorical_crossentropy',
                        optimizer='rmsprop',
                        metrics=['accuracy'])

    # Create unique ID and initialise model training thread.
    unique_id = uuid.uuid1()
    model_fit_thread = fit_model.FitModel(request.__copy__(), transfer_model, train_gen, test_gen, unique_id, model_location, epochs)
    model_fit_thread.start()

    #Model computation still run in thread and saved to blob storage, while Flask response returns successfully training process start.
    if(model_fit_thread.is_alive()):
        return f"Model successfully created and training. Model id: {unique_id}."
    else:
        return "Model training thread could not successfully be created."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    