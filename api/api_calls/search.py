from flask import Flask, Blueprint, request, jsonify
from boto3.dynamodb.conditions import Attr
from aws_clients import ImageDatabase

# Define blueprint for Flask (linked to api.py)
search_api = Blueprint('search_api', __name__)

@search_api.route('/search', methods=['GET'])
def search():
    requestData = request.get_json()

    # Check if the body has the search-keyword
    if 'search-keyword' not in requestData:
        return 'Input search-keyword attribute in the body'

    searchKeyword = requestData['search-keyword']

    searchResults = []

    # Search the characteristics of the image and the image name
    response = ImageDatabase.scan(
        FilterExpression = Attr('imageLabels').contains(searchKeyword.title()) | Attr('imageName').contains(searchKeyword)
    )

    for item in response['Items']:
        searchResults.append(item['imageName'])
        print(item['imageName'])

    return "<h1>Search request</h1>"