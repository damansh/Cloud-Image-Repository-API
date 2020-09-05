from flask import Flask, request, jsonify

from api_calls.search import search_api
from api_calls.delete import delete_api
from api_calls.add import add_api

app = Flask(__name__)
app.config["DEBUG"] = True

# @app.route('/', methods=['GET'])
# def home():
#     output = ImageDatabase.scan()

#     return output

@app.before_request
def before_request():
    if not request.get_json():
        response = {}
        response['error'] = "A JSON body request is required"
        return jsonify(response)

# Blueprints for APIs defined in respective .py files under api_calls folder
app.register_blueprint(search_api)

app.register_blueprint(delete_api)

app.register_blueprint(add_api)

app.run()

