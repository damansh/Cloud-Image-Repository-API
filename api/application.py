from flask import Flask, request, jsonify
from flask_api import status

from api_calls.search import search_api
from api_calls.delete import delete_api
from api_calls.add import add_api
from api_calls.authentication import verify_user, authentication_api

application = Flask(__name__)

@application.before_request
def before_request():
    endpoint = request.path
    method = request.endpoint

    if not endpoint == "/user" and not method == "POST":
        response = verify_user()

        if not response == 'Success':
            return response

@application.route("/")
def home():
    return "<h1>Shopify Backend Intern Challenge</h1><h2>By Daman Sharma</h2>"

# Blueprints for APIs defined in respective .py files under api_calls folder
application.register_blueprint(authentication_api)

application.register_blueprint(search_api)

application.register_blueprint(delete_api)

application.register_blueprint(add_api)

if __name__ == "__main__":
    application.run(port=5000, debug=True)
