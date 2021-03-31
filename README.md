# Cloud Image Repository API
An image repository accessed via REST API calls for the [Shopify Backend Developer Winter 2021 Intern Challenge](https://docs.google.com/document/d/1ZKRywXQLZWOqVOHC4JkF3LqdpO3Llpfk_CkZPR8bjak/edit). The hosted version of the API is hosted on Amazon Web Services (AWS) Elastic Beanstalk here: http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/.

The image repository uses AWS DynamoDB, AWS S3, AWS Rekognition, and Flask.
- DynamoDB: Holds imageName and the name of objects in an image.
- S3: File storage to hold the image (references the DynamoDB table)
- Rekognition: Provides the labels (objects) that are in an image (image object recognition)

## Installation (optional)
The API does not need to be run locally as it is already hosted. However, if you want to run this locally, execute the following steps:
- Ensure that the packages in the [requirements.txt](api/requirements.txt) file are installed using pip.
- Create a table on AWS DynamoDB called "ImageDatabase" with "imageName" as the primary key.
- Create a AWS S3 bucket and rename the name of the bucket in the [aws_clients.py](api/aws_clients.py) file.
- Ensure that your AWS credentials are set correctly on your machine.

## Routes
| HTTP Methods | "/image" endpoint                                                                                                                                                                                                                                                                                                                                                                                                                          | "/user" endpoint                                                                                                                                                                              |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| POST         | - Add a new image to the repository. <br>- Supports bulk image uploads.<br>- Specify the image permission (public or private).<br>- Secure uploads using S3 and DynamoDB.<br>- Upload file(s) in the body with the key as ```file```                                                                                                                                                                                                       | - Create a new user to upload, delete, or search images <br>- Returns a bearer token required for any "/image" endpoint call<br>- Specify username in the body with the key as ```username``` |
| GET          | - Search the repository and get S3 URL(s) to access the images.<br>- If nothing is appended to the body of the request, then retrieve all images that you can view (public or private to you).<br>- Append ```search-keyword``` to the body of the request to search based on the name of the image and the characteristics of the image.<br>- Upload an image in the body with the key as ```search-image``` to search for similar images | N/A                                                                                                                                                                                           |
| DELETE       | - Delete images from the S3 bucket and DynamoDB table that you own. Cannot delete images owned by other users.<br>- Can specify multiple images that need to be deleted.<br>- Secure deletion of images<br>- Append ```image``` in the body along with the name of images that need to be deleted (including file extension)<br>- OR append ```delete-all``` as ```true``` in the body to delete all images in the repository.             | N/A                                                                                                                                                                                           |
## Format of Request
Before making any "/image" endpoint request, make sure that a Bearer Token is added under the Authorization header. The Bearer Token can first be received by creating a new user using the "/user" endpoint and POST method.

### Uploading an image
#### One image
```
    curl -F 'file=@/path/to/file.jpg' 
          http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```

#### Multiple images
```
    curl -F 'file[]=@/path/to/fileX.jpg' 
         -F 'file[]=@/path/to/fileY.png' 
         http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```

### Other requests
The image repository API only accepts JSON data. Set the ```Content-Type``` as ```application/json```.

``` 
   curl -X GET 
        -H "Content-Type: application/json" 
        -d '{"search-keyword": "animal"}'  
        http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```

## Examples of Requests
### Search for images (GET)
#### Request

``` 
   curl -X GET 
        -H "Content-Type: application/json" 
        -d '{"search-keyword": "animal"}'  
        http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```
#### Response
```
{
    "matched-images": [
        {
            "image-name": "dog.jpg",
            "image-url": "https://img-database-bucket.s3.amazonaws.com/dog.jpg"
        },
        {
            "image-name": "cat2.jpg",
            "image-url": "https://img-database-bucket.s3.amazonaws.com/cat2.jpg"
        },
        {
            "image-name": "cat.jpg",
            "image-url": "https://img-database-bucket.s3.amazonaws.com/cat.jpg"
        }
    ]
}
```

### Add images (POST)
#### Request
```
    curl -F 'file[]=@/test_images/cat.jpg' 
         -F 'file[]=@/test_images/dog.jpg' 
         http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```

#### Response
```
{
    "added_images": [
        {
            "image": "cat.jpg",
            "status": "Added image 'cat.jpg' to the image repository."
        },
        {
            "image": "dog.jpg",
            "status": "Added image 'dog.jpg' to the image repository.""
        }
    ]
}
```

### Delete an image (DELETE)
### Request
```
  curl -X DELETE 
        -H "Content-Type: application/json" 
        -d '{"image": "cat.jpg"}'  
        http://damanshopifychallenge-env.eba-me857gfn.us-east-1.elasticbeanstalk.com/image
```

### Response
```
{
    "deleted_images": [
        {
            "image": "cat.jpg",
            "status": "Successfuly deleted image 'cat.jpg'"
        }
    ]
}
```
