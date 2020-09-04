from flask import Flask, request, jsonify
import os.path
import ntpath
import logging
from PIL import Image
import boto3
from boto3.dynamodb.conditions import Key, Attr
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

@app.route('/image', methods=['DELETE'])
def delete():
    requestData = request.get_json()
    response = {}

    # Check if the body has the image or delete-all attributes
    if 'image' not in requestData and 'delete-all' not in requestData:
        response["error"] = 'Input image or delete-all attribute in the body'
        return jsonify(response)
    
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
    response["deleted_items"] = []
    for imageToDelete in imagesToDelete:
        deletedImage= {}
        deletedImage["image"] = imageToDelete

        deletedImage["status"] = delete_image(imageToDelete)

        response["deleted_items"].append(deletedImage)

    return response

def delete_image(imageToDelete):
    # Make sure that the image exists in the database
    responseDDB = ImageDatabase.query(
        KeyConditionExpression = Key('imageName').eq(imageToDelete)
    )

    if not responseDDB["Items"]:
        return "Image '" + imageToDelete + "' does not exist in the database"
    
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


@app.route('/image', methods=['POST'])
def add():
    requestData = request.get_json()

    # Check if the body has the image-path
    if 'image-path' not in requestData:
        return 'Input image-path attribute in the body'

    imagePath = requestData['image-path']

    # Check if the image or directory exists
    if not os.path.exists(imagePath):
        return 'Image or directory does not exist'

    # Check if the path is a directory or a path to a file 
    if os.path.isdir(imagePath):
        for filename in os.listdir(imagePath):
            imageToAdd = os.path.join(imagePath, filename)

            verify_and_add_image(imageToAdd)
    elif os.path.isfile(imagePath):
        verify_and_add_image(imageToAdd)

    return 'done'

def is_file_an_image(imagePath):
    try:
        Image.open(imagePath)
    except IOError:
        return False
    return True

def verify_and_add_image(imagePath):
    fileName = ntpath.basename(imagePath)

    if not is_file_an_image(imagePath):
        print("File '" + fileName + "' is not an image")
        return

    # Make sure that the image does not exist in the database
    response = ImageDatabase.query(
        KeyConditionExpression = Key('imageName').eq(fileName)
    )

    if response["Items"]:
        print("Image with name " + fileName + " already exists in the database")
        return 

    labels = get_labels(imagePath)

    add_to_s3_and_ddb(imagePath, labels)

    print("Added image '" + fileName + "' to the image repository.")

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

