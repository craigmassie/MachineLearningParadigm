from flask import Flask, request, abort
from flask_restful import Resource, Api
from os import listdir
from os.path import isfile, join, splitext
import json
from PIL import Image
from collections import defaultdict
from sys import exc_info

app = Flask(__name__)
api = Api(app)
DATATYPE_FILE_LOCATION = "accepted_datatypes.json"

@app.route('/detectFiles', methods=['POST'])
def post():
    d = request.get_json()
    file_location = d["file_location"]
    blob_files = get_blobs_from_location(file_location)
    content_type , filtered_files= most_common_file_type(blob_files)
    verified_files = verify_images if content_type == "images" else filtered_files
    return({"content_type": content_type, "verified": verified_files})

def get_blobs_from_location(file_location):
    '''
    TODO: Implement read from Azure Blob Storage.
    '''
    return (listdir(file_location))

def valid_image(image_location):
    try:
        im = Image.open(image_location)
        im.verify()
    except:
        app.logger.info(f"{image_location} is an invalid image. Will not be used in model creation.")
        return False
    return True

def verify_images(file_location):
    image_paths = [join(file_location, f) for f in listdir(file_location)]
    verified_files = [f for f in image_paths if isfile(f)]
    verified_images = [im for im in verified_files if valid_image(im)]
    return verified_images

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
    Given a list of file names at a storage location, returns the most prevalent class of data within a folder, 
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
        for f in blobs_at_location:
            _, file_extension = splitext(f)
            if file_extension in file_extension_class:
                data_class = file_extension_class[file_extension]
                class_files[data_class].append(f)

    return get_max_class(class_files)

    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
