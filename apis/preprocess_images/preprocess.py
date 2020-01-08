from flask import Flask, request
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

@app.route('/preprocessImages', methods=['POST'])
def post():
    d = request.get_json()