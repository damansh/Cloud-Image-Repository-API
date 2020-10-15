from flask import Flask, Blueprint, request, jsonify
from flask_api import status
from boto3.dynamodb.conditions import Attr, Key
from aws_clients import UserDatabase
from uuid import uuid4
import api_calls.global_vars as global_vars

# Define blueprint for Flask (linked to api.py)
authentication_api = Blueprint('authentication_api', __name__)

# Verify user
def verify_user():
    allHeaders = request.headers 
    response = {}

    if "Authorization" not in allHeaders:
        response["error"] = 'Enter bearer token in the header or create a new user'
        return jsonify(response), status.HTTP_400_BAD_REQUEST

    bearer = allHeaders['Authorization']
    token = bearer.split()[1] 

    responseDDB = UserDatabase.query(
        KeyConditionExpression = Key('token').eq(token)
    )

    if not responseDDB['Items']:
        response["error"] = "Invalid token. Check the token or create a new user"
        return jsonify(response), status.HTTP_400_BAD_REQUEST

    currentUser = responseDDB['Items'][0]['username']
    global_vars.init(currentUser)

    return 'Success'


@authentication_api.route('/user', methods=['POST'])
def new_user():
    requestData = request.get_json()
    response = {}

    # Check if the body has username attribute
    if not requestData or 'username' not in requestData:
        response["error"] = 'Input username attribute in the body'
        return jsonify(response), status.HTTP_400_BAD_REQUEST

    username = requestData['username']

    responseDDB = UserDatabase.scan(
        FilterExpression = Attr('username').eq(username)
    )

    if responseDDB['Items']:
        response["error"] = 'Select a different username. Username already exists'
        return jsonify(response), status.HTTP_400_BAD_REQUEST

    rand_token = str(uuid4())

    responseDDB = UserDatabase.put_item(
        Item = {
            'token': rand_token,
            'username': username
        }
    )

    response["message"] = "Successfully created user '" + username + "'. Use the token to authenticate for other API calls"
    response["token"] = rand_token

    return response


    