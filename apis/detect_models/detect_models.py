from flask import Flask, request
from flask_restful import Resource, Api
import json

app = Flask(__name__)
api = Api(app)

@app.route('/detectModels', methods=['GET'])
def get():
    d = request.get_json()
    filetype = d["filetype"]
    return model_filetype_match(filetype)

def model_filetype_match(filetype):
    architectures = {}
    models = []
    with open('available_models.json') as json_file:
        data = json.load(json_file)
        for key in data["mappings"].keys():
            architectures[key] = data["mappings"][key]
        if filetype in architectures.keys():
            for architecture in architectures[filetype]:
                models.append(data["architectures"][architecture])
    return {"models": models}
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')