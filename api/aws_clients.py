import boto3

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