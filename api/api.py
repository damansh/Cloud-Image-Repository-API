from flask import Flask, request, jsonify
from flask_api import status

from api_calls.search import search_api
from api_calls.delete import delete_api
from api_calls.add import add_api

app = Flask(__name__)
app.config["DEBUG"] = True

# Make sure that there is a JSON body in the API request
@app.before_request
def before_request():
    if not request.get_json():
        response = {}
        response['error'] = "A JSON body request is required"
        return jsonify(response), status.HTTP_400_BAD_REQUEST

# Blueprints for APIs defined in respective .py files under api_calls folder
app.register_blueprint(search_api)

app.register_blueprint(delete_api)

app.register_blueprint(add_api)

app.run()

