from flask import Flask, request, abort
from flask_restful import Resource, Api
import json
import tensorflow as tf
import sys
import azure_connection
import subprocess
import os
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import lime
from lime import lime_image
from skimage.segmentation import mark_boundaries
from tensorflow.keras.preprocessing import image
import tensorflow.keras.applications.imagenet_utils as imn
import matplotlib.pyplot as plt
import autokeras as ak

app = Flask(__name__)
api = Api(app)
num_classes = 10
BLOBFUSE_MOUNT_SCRIPT = "/app/mount-blobfuse.sh"

def _request_key_required(d, request_key):
    try:
        request_value = d[request_key]
    except KeyError:
        app.logger.error(f"'{request_key}' key not found in request body. Unable to explain classification.")
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


@app.route('/explainTest', methods=['POST'])
def explain_test():
    """
    Given a request containing the model location, and image location in blob storage to explain, saves an image with the boundaries of 
    top classification to the same image directory. 
    
    Note, this is *image_location*, and not *image_url* like that of the test_model API. This corresponds to the image location in blob storage.

    Takes a POST request of the form:
    {
        "model_location": ${LOCATION_OF_BASELINE_MODEL},
        "image_location": ${LOCATION_OF_IMAGE_TO_EXPLAIN},
    }
    """
    #Mount Azure Blob Storage as a virtual file system in Docker Container
    if not os.path.isdir('/mnt/blobfusetmp/'):
        if(_mount_blobfuse()) == 400: return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    d = request.get_json()

    model_location, image_location = _request_key_required(d, "model_location"), _request_key_required(d, "image_location")
    try:
        model = tf.keras.models.load_model(model_location,custom_objects=ak. CUSTOM_OBJECTS)
        input_dimensions = _get_input_dimensions(model)
    except Exception as e:
        app.logger.error(f"Failed to load model. {e}")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

    def transform_img_fn(path_list):
        out = []
        for img_path in path_list:
            img = image.load_img(img_path, target_size=input_dimensions)
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = imn.preprocess_input(x, mode="tf")
            out.append(x)
        return np.vstack(out)

    def predict_func(images):
        prediction = model.predict(images)
        return np.squeeze(prediction)

    #Retrieve info about model and dataset from body
    if (os.path.isfile(model_location) and os.path.isfile(image_location)):
        try:
            images = transform_img_fn([image_location])
            # plt.imsave(save_location, images[0])
            explainer = lime_image.LimeImageExplainer()
            print(type(model.layers[-1]))
            if(type(model.layers[-1]) == ak.keras_layers.Sigmoid):
                explanation = explainer.explain_instance(images[0], model.predict, hide_color=0, num_samples=1000)
            else:
                explanation = explainer.explain_instance(images[0], predict_func, hide_color=0, num_samples=1000)
            temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only=False, num_features=10, hide_rest=False)
            save_location = os.path.join(os.path.dirname(model_location), "output.png")
            plt.imsave(save_location, mark_boundaries(temp / 2 + 0.5, mask))
            return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        except Exception as e:
            raise(e)
            app.logger.error(f"Failed to load model. {e}")
            return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 
    else:
        app.logger.error(f"Model or image cannot be found a specified location.")
        return json.dumps({'success':False}), 400, {'ContentType':'application/json'} 

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
