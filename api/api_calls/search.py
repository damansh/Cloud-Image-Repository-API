from flask import Flask, Blueprint, request, jsonify
from boto3.dynamodb.conditions import Attr
from aws_clients import ImageDatabase, imageDatabaseBucket

# Define blueprint for Flask (linked to api.py)
search_api = Blueprint('search_api', __name__)

@search_api.route('/image', methods=['GET'])
def search():
    requestData = request.get_json()
    response = {}

    # Check if the body has the search-keyword
    if 'search-keyword' not in requestData:
        response['error'] = 'Input search-keyword attribute in the body'
        return response

    searchKeyword = requestData['search-keyword']

    # Search the characteristics of the image and the image name
    responseDDB = ImageDatabase.scan(
        FilterExpression = Attr('imageLabels').contains(searchKeyword.title()) | Attr('imageName').contains(searchKeyword)
    )

    response["matched-images"] = []
    for item in responseDDB['Items']:
        matchedImage = {}
        
        matchedImage['image-name'] = item['imageName']
        matchedImage['image-url'] = "https://%s.s3.amazonaws.com/%s" % (imageDatabaseBucket, item['imageName'])
        
        response["matched-images"].append(matchedImage)

    return response