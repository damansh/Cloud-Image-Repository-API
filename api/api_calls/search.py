from flask import Flask, Blueprint, request, jsonify
from flask_api import status
from boto3.dynamodb.conditions import Attr
from aws_clients import ImageDatabase, imageDatabaseBucket
import os.path
from api_calls.add import is_file_an_image, get_labels

# Define blueprint for Flask (linked to api.py)
search_api = Blueprint('search_api', __name__)

@search_api.route('/image', methods=['GET'])
def search():
    requestData = request.get_json()
    response = {}

    # Check if the body has the search-keyword
    if 'search-keyword' not in requestData and 'search-image' not in requestData:
        response['error'] = 'Input search-keyword or search-image attribute in the body'
        return response, status.HTTP_400_BAD_REQUEST

    if 'search-image' in requestData:
        image_search(requestData['search-image'], response)
    elif 'search-keyword' in requestData:
        text_search(requestData['search-keyword'], response)
    
    if hasattr(response , 'error'):
        return response, status.HTTP_400_BAD_REQUEST
    else:
        return response

# Get the labels from the provided image using AWS Rekognition and check if there is a match
# in the database
def image_search(imagePath, response):
    if not os.path.exists(imagePath):
        response["error"] =  'Image or directory does not exist'
        return jsonify(response)
    
    if os.path.isdir(imagePath):
        response["error"] =  'Filepath provided using search-image is a directory. Enter a filepath to an image'
        return jsonify(response)

    if not is_file_an_image(imagePath):
        response["error"] =  'Image cannot be opened. Check the image file.'
        return jsonify(response)
    
    labels = get_labels(imagePath)

    preparedFilterExpression = ""
    preparedExpressionAttrValues = {}

    for idx, label in enumerate(labels):
        if preparedFilterExpression:
            preparedFilterExpression += " or "
        
        preparedFilterExpression += "contains(imageLabels, :label" + str(idx) + ")"
        preparedExpressionAttrValues[":label" + str(idx)] = label

    responseDDB = ImageDatabase.scan(
        FilterExpression = preparedFilterExpression,
        ExpressionAttributeValues = preparedExpressionAttrValues
    )

    populate_response(responseDDB, response)

# Use the inputted text to see if there is a matching image based on the image name and characteristics
# of the image
def text_search(searchKeyword, response):
    # Search the characteristics of the image and the image name
    responseDDB = ImageDatabase.scan(
        FilterExpression = Attr('imageLabels').contains(searchKeyword.title()) | Attr('imageName').contains(searchKeyword)
    )

    populate_response(responseDDB, response)

# Populate the API response with the image URL
def populate_response(responseDDB, response):
    response["matched-images"] = []
    for item in responseDDB['Items']:
        matchedImage = {}
        
        matchedImage['image-name'] = item['imageName']
        matchedImage['image-url'] = "https://%s.s3.amazonaws.com/%s" % (imageDatabaseBucket, item['imageName'])
        
        response["matched-images"].append(matchedImage)