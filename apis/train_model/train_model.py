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
import zipfile
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import tensorflow.keras.applications.imagenet_utils as imn
import os,sys
import lime
from lime import lime_image
from skimage.segmentation import mark_boundaries
from tensorflow.keras.preprocessing import image
import tensorflow.keras.applications.imagenet_utils as imn
import matplotlib.pyplot as plt
import train_auto
import autokeras as ak

app = Flask(__name__)
api = Api(app)
num_classes = 10
BLOBFUSE_MOUNT_SCRIPT = "/app/mount-blobfuse.sh"

def _request_key_required(d, request_key):
    try:
        request_value = d[request_key]
    except KeyError:
        app.logger.error(f"'{request_key}' key not found in request body. Unable to find begin training.")
        abort(400)
    return request_value

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

def _load_dataset_into_gen(dataset_location, expected_model_input_size):
    filename = os.path.basename(dataset_location).split('.')[0]
    if(dataset_location.endswith(".zip")):
        extraction_dir = os.path.splitext(dataset_location)[0]
        if (not os.path.isdir(extraction_dir)):
            app.logger.info(f"Found zip file, extracting to: {extraction_dir}")
            try:
                app.logger.info("Attempting extract.")
                with zipfile.ZipFile(dataset_location,"r") as zip_ref:
                    zip_ref.extractall(path=extraction_dir)
            except Exception as e:
                app.logger.error(f"Unable to extract zip file due to: {e}")
        dataset_location = os.path.join(extraction_dir, filename)
    app.logger.info("Attempting to load dataset into generator.")
    training_data_location = os.path.join(dataset_location, "train")
    test_data_location = os.path.join(dataset_location, "test")
    if not os.path.exists(training_data_location):
        app.logger.error(f"Unable to find training data directory at location {training_data_location}")
    if not os.path.exists(test_data_location):
        app.logger.error(f"Unable to find training data directory at location {test_data_location}")

    train_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
    train_generator = train_datagen.flow_from_directory(training_data_location, target_size=expected_model_input_size, shuffle=True, seed=42, batch_size=16, subset='training')

    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator()
    test_generator = test_datagen.flow_from_directory(test_data_location, target_size=expected_model_input_size, shuffle=True, seed=42, batch_size=16)
    return train_generator, test_generator

def _mount_blobfuse():
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

def _url_to_img(model, image_url, model_location):
    input_dimensions = _get_input_dimensions(model)
    app.logger.info(f"id: {input_dimensions}")
    r = requests.get(image_url, stream=True)
    r.raw.decode_content = True # Content-Encoding
    img = Image.open(r.raw)
    if img.size != input_dimensions:
        img = img.resize(input_dimensions, Image.LANCZOS)
    save_location = os.path.join(os.path.dirname(model_location), "predict.png")
    img.save(save_location)
    x = tf.keras.preprocessing.image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    return x

def _request_key_optional(d, request_key):
    try:
        request_value = d[request_key]
        return request_value
    except KeyError:
        return None


@app.route('/trainModel', methods=['POST'])
def train_model():
    """
    Given environment variables specifiying Azure connection, and model/dataset location initialises transfer learning training.

    Takes a POST request of the form:
    {
        "model_location": ${LOCATION_OF_BASELINE_MODEL},
        "dataset_location": ${LOCATION_OF_TRAIN_TEST_DATA},
        "epochs": ${NUM_OF_TRAINING_EPOCHS}
        "auto_type": ${AUTO_KERAS_TYPE}
    }
    """
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    # if not os.path.isdir('/mnt/blobfusetmp/'):
    #     if(_mount_blobfuse()) == 400: return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    d = request.get_json()
    unique_id = uuid.uuid1()

    #Retrieve info about model and dataset from body
    model_location, dataset_location, epochs, auto_type, trials = _request_key_required(d, "model_location"), _request_key_required(d, "dataset_location"), _request_key_required(d, "epochs"), _request_key_optional(d, "auto_type"), _request_key_optional(d, "trials")

    if (auto_type and epochs and trials):
        #model_location in this instance is the parent dir to save under
        auto_fit_thread = train_auto.AutoMLTrain(request.__copy__(), model_location, dataset_location, unique_id, auto_type, app.logger, epochs, trials)
        auto_fit_thread.start()
        if(auto_fit_thread.is_alive()):
            auto_fit_thread.join()
            return f"Auto model successfully created and training. Model id: {str(unique_id)}."
        else:
            return "Model training thread could not successfully be created."

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

    transfer_model.compile(loss='categorical_crossentropy',
                        optimizer='rmsprop',
                        metrics=['accuracy'])

    app.logger.info(f"Model Summary: {transfer_model.summary()}")

    # Create unique ID and initialise model training thread.
    app.logger.info(f"ci {train_gen.class_indices}")
    model_fit_thread = fit_model.FitModelFromGenerators(request.__copy__(), transfer_model, train_gen, test_gen, unique_id, model_location, epochs)
    model_fit_thread.start()
    app.logger.info(f"Output directory: {os.path.join(os.path.dirname(model_location), str(unique_id))}")
    class_file_loc = os.path.join(os.path.dirname(model_location), str(unique_id), "classes.npy")
    app.logger.info(f"Saving numpy array to: {class_file_loc}")
    try:
        if not(os.path.isdir(os.path.dirname(class_file_loc))):
            os.makedirs(os.path.dirname(class_file_loc), exist_ok = True) 
        np.save(class_file_loc, train_gen.class_indices, allow_pickle=True)
    except Exception as e:
        app.logger.info(f"Failed to save classes {e}")
    #Model computation still run in thread and saved to blob storage, while Flask response returns successfully training process start.
    if(model_fit_thread.is_alive()):
        # model_fit_thread.join()
        return f"Model successfully created and training. Model id: {str(unique_id)}."
    else:
        return "Model training thread could not successfully be created."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
