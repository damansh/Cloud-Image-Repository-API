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

    # If the user does not provide an image to search based on or a search query, retrieve all images
    if 'search-image' not in request.files and ((not requestData) or (requestData and 'search-keyword' not in requestData)):
        get_all_images(response)
        return response

    if request.files and 'search-image' in request.files:
        image_search(request.files["search-image"], response)
    elif requestData and 'search-keyword' in requestData:
        text_search(requestData['search-keyword'], response)
    
    if hasattr(response , 'error'):
        return response, status.HTTP_400_BAD_REQUEST
    else:
        return response

# Get the labels from the provided image using AWS Rekognition and check if there is a match
# in the database
def image_search(uploadedFile, response):
    fileName = uploadedFile.filename

    if not "image" in uploadedFile.mimetype :
        return "File '" + fileName + "' is not an image"
    
    labels = get_labels(uploadedFile)

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

def get_all_images(response):
    responseDDB = ImageDatabase.scan()
    print(responseDDB)
    populate_response(responseDDB, response)

# Populate the API response with the image URL
def populate_response(responseDDB, response):
    response["matched-images"] = []
    for item in responseDDB['Items']:
        matchedImage = {}
        
        matchedImage['image-name'] = item['imageName']
        matchedImage['image-url'] = "https://%s.s3.amazonaws.com/%s" % (imageDatabaseBucket, item['imageName'])
        
        response["matched-images"].append(matchedImage)