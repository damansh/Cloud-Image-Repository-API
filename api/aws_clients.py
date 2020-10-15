import boto3

# ImageDatabase AWS DynamoDB table
imageTableName = "ImageDatabase"
ddb = boto3.resource('dynamodb', region_name='us-east-1')
ImageDatabase = ddb.Table(imageTableName)

# Users AWS DynamoDB table
userTableName = "UserDatabase"
UserDatabase = ddb.Table(userTableName)

# AWS Rekognition client 
rekognitionClient = boto3.client('rekognition', region_name='us-east-1')

# AWS S3 bucket 
imageDatabaseBucket = 'img-database-bucket'
s3Client = boto3.client('s3', region_name='us-east-1')
s3Resource = boto3.resource('s3', region_name='us-east-1')