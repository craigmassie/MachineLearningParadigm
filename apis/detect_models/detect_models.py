from flask import Flask, request
from flask_restful import Resource, Api
import json

app = Flask(__name__)
api = Api(app)
ARCHITECTURE_FILE_LOCATION = "available_models.json"

@app.route('/detectModels', methods=['GET'])
def get():
    d = request.get_json()
    filetype = d["filetype"]
    return model_filetype_match(filetype)

def model_filetype_match(filetype):
    '''
    Given the filetype provided, determines which type of architectures are suitable.
    Subsequently, based on the architcture, will return pre-existing models of such, and their location.
    '''
    architectures = {}
    models = []
    with open(ARCHITECTURE_FILE_LOCATION) as json_file:
        available_models = json.load(json_file)
        #architectures takes on the form: {File Type Class: [List of architectures]}
        architectures = available_models["mappings"]
        if filetype in architectures.keys():
            for architecture in architectures[filetype]:
                models.append(available_models["architectures"][architecture])
        if models == []:
            app.logger.info(f"There exist no models with the filetype: {filetype}")
    return {"models": models}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')