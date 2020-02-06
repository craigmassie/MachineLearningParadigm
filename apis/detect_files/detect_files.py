from flask import Flask, request, abort
from flask_restful import Resource, Api
import os
from os.path import isfile, join, splitext
import json
from collections import defaultdict
from sys import exc_info
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

app = Flask(__name__)
api = Api(app)
DATATYPE_FILE_LOCATION = "accepted_datatypes.json"

'''
ROUTES
'''

@app.route('/detectFiles', methods=['POST'])
def post():
    d = request.get_json()
    try:
        container_name = d["container_name"]
    except KeyError:
        app.logger.error(f"'container_name' key not found in request body. Unable to determine file type without location.")
        abort(400)
    blob_service_client, container_client = init_connection(container_name)
    blob_objects = get_blobs_from_container(container_client)
    content_type , filtered_blobs= most_common_file_type(blob_objects)
    '''Verification avoided for now. See function comments'''
    # verified_blobs = verify_images(filtered_blobs, blob_service_client) if content_type == "images" else filtered_blobs
    filtered_names = [blob.name for blob in filtered_blobs]
    return({"content_type": content_type, "verified": filtered_names})

'''
HELPER FUNCTIONS
'''

def init_connection(container_name):
    if (os.environ.get("AZURE_STORAGE_CONNECTION_STRING") is not None):
        connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    else:
        app.logger.error(f"'AZURE_STORAGE_CONNECTION_STRING' environment variable not set.")
        abort(400)
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(container_name)
    except ConnectionError as err:
        app.logger.error(f"'AZURE_STORAGE_CONNECTION_STRING' environment variable not set. {err}")
        abort(400)
    return blob_service_client, container_client

def get_blobs_from_container(container_client):
    return container_client.list_blobs()

def valid_image(blob):
    try:
        image = Image.open(io.BytesIO(blob))
        im.verify()
    except:
        # app.logger.info(f"{image_location} is an invalid image. Will not be used in model creation.")
        return False
    return True

def verify_images(blob_objects, blob_service_client):
    '''
    Reading deprecated in azure storage blob 12(?)
    See: https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/storage/azure-storage-blob/azure/storage/blob/aio/_blob_service_client_async.py
    TODO: Check if such a non verbose way is possible with the new API.
    '''
    verified = []
    for blob in blob_objects:
        blob = blob_service_client.get_blob_client("testuploads", blob.name)
        blob = blob.download_blob().readall()
        if valid_image(blob):
            verified.append(blob)
    return verified

def get_max_class(d):  
    '''
    Given a dictionary, returns the key, value pair with the longest length value.
    '''
    try:
        max_class = max(d, key=lambda k: len(d[k]))
        return max_class, d[max_class]
    except ValueError as e:
        app.logger.error(f"No acceptable files exists. Unable to procees with subsequent workflow. {e}" )
        abort(400)

def most_common_file_type(blobs_at_location):
    '''
    Given a list of blobs at a storage location, returns the most prevalent class of data within a folder, 
    alongisde the files of that class.
    '''
    class_files = defaultdict(list)
    with open(DATATYPE_FILE_LOCATION) as json_file:
        accepted_datatypes = json.load(json_file)
        file_extension_class = {}
        #JSON traversal to determine acceptable data types.
        for data_class in accepted_datatypes.keys():
            for accepted_extension in accepted_datatypes[data_class]:
                file_extension_class[accepted_extension] = data_class

        #Assign files to their respective class
        for blob in blobs_at_location:
            _, file_extension = splitext(blob.name)
            if file_extension in file_extension_class:
                data_class = file_extension_class[file_extension]
                class_files[data_class].append(blob)
    return get_max_class(class_files)

    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
