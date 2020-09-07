from flask import Flask, Blueprint, request, jsonify
from flask_api import status
from boto3.dynamodb.conditions import Attr, Key
import os.path
import ntpath
from PIL import Image
from aws_clients import ImageDatabase, rekognitionClient, s3Client, s3Resource, imageDatabaseBucket

# Define blueprint for Flask (linked to api.py)
add_api = Blueprint('add_api', __name__)

@add_api.route('/image', methods=['POST'])
def add():
    requestData = request.get_json()
    response = {}

    # Check if the body has the image-path
    if 'file' not in request.files:
        response["error"] = 'Input file attribute in the body'
        return jsonify(response), status.HTTP_400_BAD_REQUEST

    uploaded_files = request.files.getlist("file")

    response["added_images"] = []
    for uploaded_file in uploaded_files:
        addedImage= {}
        addedImage["image"] = uploaded_file.filename

        addedImage["status"] = verify_and_add_image(uploaded_file)

        response["added_images"].append(addedImage)

    return jsonify(response)

# Check whether the file is an image prior to upload
def is_file_an_image(imagePath):
    try:
        Image.open(imagePath)
    except IOError:
        return False
    return True

# Verify that the file is an image and the image doesn't currently exist in the database.
# Then, upload the image to the DynamoDB database and the S3 bucket
def verify_and_add_image(uploadedFile):
    fileName = uploadedFile.filename

    if not "image" in uploadedFile.mimetype :
        return "File '" + fileName + "' is not an image"

    # Make sure that the image does not exist in the database
    response = ImageDatabase.query(
        KeyConditionExpression = Key('imageName').eq(fileName)
    )

    if response["Items"]:
        return "Image with name " + fileName + " already exists in the database"

    labels = get_labels(uploadedFile)

    add_to_s3_and_ddb(uploadedFile, labels)

    return "Added image '" + fileName + "' to the image repository."

# Open the image and upload the file to S3. Then, add item to DynamoDB table
def add_to_s3_and_ddb(uploadedFile, labels):
    fileName = uploadedFile.filename

    uploadedFile.seek(0)
    s3Client.upload_fileobj(uploadedFile, imageDatabaseBucket, fileName)            

    s3Resource.Object(imageDatabaseBucket, fileName).wait_until_exists()

    response = ImageDatabase.put_item(
        Item = {
            'imageName': fileName,
            'imageLabels': labels
        }
    )

# Use AWS Rekognition to get the labels of the image. Used to search for items in an image with the search API
def get_labels(uploadedFile):
    response = rekognitionClient.detect_labels(Image={'Bytes': uploadedFile.read()})

    labels = []

    for label in response["Labels"]:
        labels.append(label['Name'])

    return labels


