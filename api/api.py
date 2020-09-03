from flask import Flask, request, jsonify
import os.path
import ntpath
import logging
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
app.config["DEBUG"] = True

# AWS DynamoDB table
tableName = "ImageDatabase"
ddb = boto3.resource('dynamodb')
ImageDatabase = ddb.Table(tableName)

# AWS Rekognition client 
rekognitionClient = boto3.client('rekognition')

# AWS S3 bucket 
imageDatabaseBucket = 'img-database-bucket'
s3Client = boto3.client('s3')
s3Resource = boto3.resource('s3')

@app.route('/', methods=['GET'])
def home():
    output = ImageDatabase.scan()

    return output

@app.route('/search', methods=['GET'])
def seatch():
    return "<h1>Search request</h1>"


@app.route('/add', methods=['GET'])
def add():
    requestData = request.get_json()

    # Check if the body has the image-path
    if 'image-path' not in requestData:
        return 'Input image-path attribute in the body'

    imagePath = requestData['image-path']

    # Check if the image or directory exists
    if not os.path.exists(imagePath):
        return 'Image or directory does not exist'

    fileName = ntpath.basename(imagePath)

    # Make sure that the image does not exist in the database
    response = ImageDatabase.query(
        KeyConditionExpression = Key('imageName').eq(fileName)
    )

    if response["Items"]:
        return "Image with name " + fileName + " already exists in the database"

    labels = get_labels(imagePath)

    add_to_s3_and_ddb(imagePath, labels)

    return 'done'


def add_to_s3_and_ddb(imagePath, labels):
    fileName = ntpath.basename(imagePath)

    with open(imagePath, 'rb') as image:
        s3Client.upload_fileobj(image, imageDatabaseBucket, fileName)            

    s3Resource.Object(imageDatabaseBucket, fileName).wait_until_exists()

    response = ImageDatabase.put_item(
        Item = {
            'imageName': fileName,
            'imageLabels': labels
        }
    )


def get_labels(imagePath):
    with open(imagePath, 'rb') as image:
        response = rekognitionClient.detect_labels(Image={'Bytes': image.read()})

    labels = []

    for label in response["Labels"]:
        labels.append(label['Name'])

    return labels

app.run()

