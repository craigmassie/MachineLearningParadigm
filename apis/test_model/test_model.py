import json
import os
import subprocess

import autokeras as ak
import numpy as np
import requests
import tensorflow as tf
from flask import Flask, abort, request
from flask_restful import Api, Resource
from PIL import Image
from tensorflow.keras.preprocessing import image

app = Flask(__name__)
api = Api(app)
BLOBFUSE_MOUNT_SCRIPT = "/app/mount-blobfuse.sh"

def _request_key_required(d, request_key):
    try:
        request_value = d[request_key]
    except KeyError:
        app.logger.error(f"'{request_key}' key not found in request body. Unable to find test model.")
        abort(400)
    return request_value

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

def _mount_blobfuse():
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    try:
        if os.path.isfile(BLOBFUSE_MOUNT_SCRIPT):
            subprocess.call([BLOBFUSE_MOUNT_SCRIPT], shell=True)
        else:
            raise FileExistsError(f"{BLOBFUSE_MOUNT_SCRIPT} not found.")
    except Exception as e:
        app.logger.error(f"Issue with running blobfuse mounting script {BLOBFUSE_MOUNT_SCRIPT}, please ensure that file exists \
            and that sufficient privileges are given to all for execution. {e}")
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

def _get_formatted_prediction(model_location, prediction):
    if (type(prediction) == list):
            prediction = [float(x) for x in prediction]
    elif (type(prediction) != float):
        app.logger.error(f"Failed to load predictions, expected type list or float. {e}")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 
    classes_file = os.path.join(os.path.dirname(model_location), "classes.npy")
    if os.path.isfile(classes_file):
        class_indices = np.load(classes_file, allow_pickle = True).item()
        class_keys = [x.strip() for x in list(class_indices.keys())]
        if(type(prediction) == float):
            prediction = [1.0 - prediction, prediction]
        results_dict = { k:v for (k,v) in zip(class_keys, prediction)}
        return results_dict
    else:
        if(type(prediction) == float):
            prediction = [1.0 - prediction, prediction]
        results_dict = { k:v for (k,v) in enumerate(prediction)}
        return results_dict 

@app.route('/testModel', methods=['POST'])
def test_model():
    """
    Given a request containing the model location, and image to predict, return a key/value pair of prediction class 
    and probability of that image belonging to the class.

    Takes a POST request of the form:
    {
        "model_location": ${LOCATION_OF_BASELINE_MODEL},
        "image_url": ${URL_OF_IMAGE_TO_PREDICT},
    }
    """
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    if not os.path.isdir('/mnt/blobfusetmp/'):
        if(_mount_blobfuse()) == 400: return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    d = request.get_json()

    #Retrieve info about model and dataset from body
    model_location, image_url = _request_key_required(d, "model_location"), _request_key_required(d, "image_url")

    if (not os.path.isfile(model_location)): 
        app.logger.error(f"Failed to find model at given location.")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    if(model_location.endswith('.pb')):
        model_location = os.path.dirname(model_location)

    try:
        model = tf.keras.models.load_model(model_location, custom_objects=ak. CUSTOM_OBJECTS)
    except Exception as e:
        raise(e)
        app.logger.error(f"Failed to load model. {e}")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    try:    
        image = _url_to_img(model, image_url, model_location)
    except Exception as e:
        raise(e)
        app.logger.error(f"Failed to load image from url. {e}")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    try:    
        prediction = np.squeeze(model.predict(image)).tolist()
        return _get_formatted_prediction(model_location, prediction)
    except Exception as e:
        raise(e)
        app.logger.error(f"Failed to classify image. {e}")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
