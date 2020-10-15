from flask import Flask, Blueprint, request, jsonify
from flask_api import status
from boto3.dynamodb.conditions import Attr, Key
from aws_clients import ImageDatabase, s3Client, imageDatabaseBucket
import api_calls.global_vars as global_vars

# Define blueprint for Flask (linked to api.py)
delete_api = Blueprint('delete_api', __name__)

@delete_api.route('/image', methods=['DELETE'])
def delete():
    requestData = request.get_json()
    response = {}

    # Check if the body has the image or delete-all attributes
    if not requestData or ('image' not in requestData and 'delete-all' not in requestData):
        response["error"] = 'Input image or delete-all attribute in the body'
        return jsonify(response), status.HTTP_400_BAD_REQUEST
    
    imagesToDelete = []

    # Populate the imagesToDelete list
    if 'delete-all' in requestData and requestData['delete-all'] == 'true':
        allImages = ImageDatabase.scan()
        for image in allImages["Items"]:
            imagesToDelete.append(image["imageName"])
    elif 'image' in requestData:
        if isinstance(requestData['image'], list):
            imagesToDelete = requestData['image']
        else:
            imagesToDelete.append(requestData['image']) 

    # Delete the specified images
    response["deleted_images"] = []
    for imageToDelete in imagesToDelete:
        deletedImage= {}
        deletedImage["image"] = imageToDelete

        deletedImage["status"] = delete_image(imageToDelete)

        response["deleted_images"].append(deletedImage)

    return response

# Delete the image from S3 and DynamoDB
def delete_image(imageToDelete):
    # Make sure that the image exists in the database
    responseDDB = ImageDatabase.query(
        KeyConditionExpression = Key('imageName').eq(imageToDelete)
    )

    if not responseDDB["Items"]:
        return "Image '" + imageToDelete + "' does not exist in the database"
    
    if responseDDB["Items"][0]["uploadedBy"] != global_vars.currentUser:
        return "Image '" + imageToDelete + "' not uploaded by " + global_vars.currentUser + ". Image not deleted"

    responseS3 = s3Client.delete_object(
        Bucket = imageDatabaseBucket,
        Key = imageToDelete
    )

    if responseS3['ResponseMetadata']['HTTPStatusCode'] != 204:
        return "Error while deleting the image '" + imageToDelete + "' from the S3 bucket"

    responseDDB = ImageDatabase.delete_item(
        Key = {
            "imageName": imageToDelete
        }
    )

    if responseDDB['ResponseMetadata']['HTTPStatusCode'] != 200:
        return "Error while deleting database entry for the image '" + imageToDelete + "' from the DynamoDB table"
    
    return "Successfuly deleted image '" + imageToDelete + "'"
