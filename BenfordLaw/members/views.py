from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .benford2 import benfordLaw
from django.views.decorators.csrf import csrf_exempt
from openpyxl import load_workbook
from datetime import datetime
import boto3
from botocore.exceptions import ClientError  
import json
#<------------------Generating a Unique Filename---------------------------->
def generate_unique_filename():
  timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
  return f"{timestamp}"

#<------------------Creating a bucket by taking bucket_name ----------------------->
def create_bucket(s3_client, bucket_name):
  try:
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created successfully")
  except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
      print(f"Bucket '{bucket_name}' already exists. Proceeding...")
    else:
      print(f"Error creating bucket: {e}")

#<--------------------Generating a Presigned URL----------------------------------->
def generate_presigned_url(s3_client, bucket_name, filename, expiration=3600):
  try:
    object_key = filename  # Replace with desired filename in bucket
    presigned_url = s3_client.generate_presigned_url(
        ClientMethod='get_object' if expiration < 0 else 'put_object',
        Params={'Bucket': bucket_name, 'Key': object_key},
        ExpiresIn=expiration  # URL expiration time in seconds (set to -1 for download)
    )
    return presigned_url
  except ClientError as e:
    print(f"Error generating pre-signed URL: {e}")
    return None
  
#<-----------------------Uploading the file in S3 Bucket---------------------------->
def upload_file_with_presigned_url(s3_client, bucket_name, filename, local_file_path):
  try:
    create_bucket(s3_client, bucket_name)  # Create bucket if it doesn't exist
    upload_url = generate_presigned_url(s3_client, bucket_name, filename)
    if not upload_url:
      return None
    local_file_path.seek(0)  
    s3_client.upload_fileobj(local_file_path, bucket_name, filename)
    print(f"File '{filename}' uploaded successfully!")
    download_url = generate_presigned_url(s3_client, bucket_name, filename, expiration=-1)  # Set expiration to -1 for download
    return download_url

  except Exception as e:
    print(f"Error uploading file: {e}")
    return None

#<-----------------------Making a Queue--------------------------------------->
def make_queue(sqs_client, queue_name):
  try:
    # Attempt to get the queue attributes
    response = sqs_client.get_queue_attributes(QueueUrl=queue_name, AttributeNames=['QueueArn'])
    print(f"Queue '{queue_name}' already exists. Url: {response['Attributes']['QueueArn']}")
    response = sqs_client.get_queue_url(QueueName=queue_name)
    return (response['QueueUrl'])
  except ClientError as e:
    print(e.response)
    print(f"Queue '{queue_name}' does not exist. Creating...")
    response = sqs_client.create_queue(QueueName=queue_name)
    print(f"Queue created successfully! Url: {response['QueueUrl']}")
    return response['QueueUrl']  # Return newly created queue URL


#<-------------------------Defining variables----------------------------------->
queue_name = 'exel_file_storer'
endpoint_url = 'http://localhost:4566'
endpoint_urlsqs = 'http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-queue2'
aws_access_key_id = 'test'
aws_secret_access_key = 'test'


s3 = boto3.client(
service_name='s3',
aws_access_key_id=aws_access_key_id,
aws_secret_access_key=aws_secret_access_key,
endpoint_url=endpoint_url
)

@csrf_exempt
def upload_excel2(request):
    if request.method == 'POST' and request.FILES:
        # Assuming you have only one file upload field in your form
        uploaded_files = list(request.FILES.values())
        if not uploaded_files:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        try:
            excel_file = uploaded_files[0]
            if not excel_file.name.endswith('.xlsx'):
                return JsonResponse({'error': 'Uploaded file is not in Excel format'}, status=400)
            filename = generate_unique_filename() + '.xlsx'
            bucket_name = 'exelfile'
            x = upload_file_with_presigned_url(s3,bucket_name,filename,excel_file)
            if(x):
                try:
                  sqs = boto3.client('sqs',region_name='us-east-1',aws_access_key_id='access_key', aws_secret_access_key='secret_key', endpoint_url=endpoint_urlsqs)
                  message_body = {
                    'filename': filename,
                    'presigned_url': x
                  }
                  json_message_body = json.dumps(message_body)
                  Queue_Url = make_queue(sqs_client=sqs,queue_name=queue_name)
                  response = sqs.send_message(MessageBody = json_message_body,QueueUrl = Queue_Url)
                  print(f"Sent message to SQS queue (ID: {response['MessageId']})")
                except ClientError as e:
                  print(f"Error sending message to SQS: {e}")
                  return JsonResponse({'error': 'Error processing uploaded file'}, status=500)
            modified_file_path = benfordLaw(x)   
            # print(x)
            print(modified_file_path)
            y = upload_file_with_presigned_url(s3,bucket_name,filename,modified_file_path)
            return JsonResponse({'link':y})
        except Exception as e:
            return JsonResponse({'error': f'Error saving Excel file: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': 'No file uploaded'}, status=400)    
        
