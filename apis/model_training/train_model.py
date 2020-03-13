from flask import Flask, request, abort
from flask_restful import Resource, Api
import json
import tensorflow as tf
import sys
from tensorflow.keras.datasets import cifar10
import azure_connection
'''TODO: remove all preprocessing to seperate API'''
from sklearn.model_selection import train_test_split
import subprocess
import os

app = Flask(__name__)
api = Api(app)
batch_size = 128
num_classes = 10
epochs = 5
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

def _add_classifier_to_model(model_layers, num_classes):
    flatten_layer = tf.keras.layers.Flatten()(model_layers[-1])
    classifier = tf.keras.layers.Dense(num_classes, activation='softmax')(flatten_layer)
    model_layers.append(flatten_layer)
    model_layers.append(classifier)
    return model_layers

def _get_model(model_location, image_shape):
    model_loaded = tf.keras.models.load_model(model_location)
    model_correct_input = _alter_model_input_size(model_loaded, image_shape)
    model_with_top = _add_classifier_to_model(model_correct_input, 10)
    return tf.keras.Model(model_with_top[0], model_with_top[-1])

def get_image_shape(dataset_location):
    #TODO
    image_shape = (32,32,3)
    #Validation of input shape
    return image_shape

@app.route('/trainModel', methods=['POST'])
def post():
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    try:
        if os.path.isfile(BLOBFUSE_MOUNT_SCRIPT):
            subprocess.call([BLOBFUSE_MOUNT_SCRIPT], shell=True)
    except Exception as e:
        app.logger.error(f"Issue with running blobfuse mounting script {BLOBFUSE_MOUNT_SCRIPT}, please ensure that file exists \
            and that sufficient priveledges are given to all for execution. {e}")
        return(400)

    # user_defined_mount_path = os.getenv("AZURE_MOUNT_POINT")
    # if os.path.isdir(user_defined_mount_path):
    #     app.logger.info(f"Azure Blob Storage successfully mounted to container at {user_defined_mount_path}")
    # else:
    #     app.logger.error(f"Unable to find a successful Azure Storage mount at {user_defined_mount_path}")
    #     return(400)

    d = request.get_json()

    #Retrieve info about model and dataset from body
    model_location, dataset_location = _request_key_exists(d, "model_location"), _request_key_exists(d, "dataset_location")
    image_shape = get_image_shape(dataset_location)

    transfer_model = _get_model(model_location, image_shape)
    
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    y_train = tf.keras.utils.to_categorical(y_train, num_classes)
    y_test = tf.keras.utils.to_categorical(y_test, num_classes)

    app.logger.info(transfer_model.summary())

    transfer_model.compile(loss='categorical_crossentropy',
                        optimizer='rmsprop',
                        metrics=['accuracy'])

    transfer_model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))

    score = transfer_model.evaluate(x_test, y_test, verbose=0)
    return('Test loss:', score[0], 'Test accuracy:', score[1])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    