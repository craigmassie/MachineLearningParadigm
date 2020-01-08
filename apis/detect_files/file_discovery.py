from flask import Flask, request
from flask_restful import Resource, Api
from os import listdir
from os.path import isfile, join
import json
from PIL import Image

app = Flask(__name__)
api = Api(app)

@app.route('/detectFiles', methods=['POST'])
def post():
    d = request.get_json()
    file_location = d["file_location"]
    blob_files = get_blobs_from_location(file_location)
    content_type , filtered_files= most_common_file_type(blob_files)
    verified_files = []
    if content_type == "images":
        verified_files = verify_images(file_location)
    elif content_type == "structured_data":
        verified_files = filtered_files
    return({"content_type": content_type, "verified": verified_files})

def get_blobs_from_location(file_location):
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

def most_common_file_type(file_location):
    '''
    Returns the most prevalent class of data within a folder.
    '''
    d = {}
    with open('accepted_datatypes.json') as json_file:
        data = json.load(json_file)
        d = {}
        file_type_map = {}
        for f in file_location:
            for attribute in data.keys():
                for file_type in data[attribute]:
                    file_type_map[file_type] = attribute
                    if f.endswith(file_type):
                        if attribute in d:
                            d[attribute].append(f)
                        else:
                            d[attribute] = [f]

    max_files = []
    max_name = ""
    for dtype in d:
        if len(d[dtype]) > len(max_files):
            max_files = d[dtype]
            max_name = dtype
    return (max_name, max_files)

    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
