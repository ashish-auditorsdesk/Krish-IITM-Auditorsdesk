from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import io
import fitz  #pymupdf
from .bill_automation import ocr_by_paddleocr
from datetime import datetime
import boto3
from botocore.exceptions import ClientError  

#<------------------Generating a Unique Filename---------------------------->
def generate_unique_filename(original_filename):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extension = original_filename.split('.')[-1]  # Get the original file extension
    return f"{timestamp}.{extension}"

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


@csrf_exempt
def ocr(request):
    # print(request.FILES.values())
    if request.method == 'POST' and request.FILES:
        uploaded_files = list(request.FILES.values())
        print(uploaded_files)
        if not uploaded_files:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        try:
            if not (uploaded_files[0].name.endswith('.PDF') or  uploaded_files[0].name.endswith('.pdf') ):
               return JsonResponse({'error': 'Uploaded file is not in pdf format'}, status=400)
            file_name = generate_unique_filename(uploaded_files[0].name) 
            print("you are on right track")
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.LOCALSTACK_ENDPOINT_URL
            )
            upload_url = upload_file_with_presigned_url(s3_client, 'my-bucket', file_name, uploaded_files[0])
            print(upload_url)
            if upload_url:
                response = requests.get(upload_url)
                pdf_content = io.BytesIO(response.content)
                print(pdf_content)
                document = fitz.open(stream=pdf_content, filetype="pdf")

                # for image in images:
                for i in range(document.page_count):
                    page = document.load_page(i)
                    pix = page.get_pixmap()  # Convert page to an image
                    image = pix.tobytes("png")
                # Process the image using your OCR function
                    try:
                        ocr_result = ocr_by_paddleocr(image)
                    except:
                        return JsonResponse("error from here ")                                                                                    
                return JsonResponse({'message': 'File uploaded successfully', 'url': upload_url,'result':ocr_result})
            else:
                return JsonResponse({'error': 'Failed to upload file'}, status=500)
        except:
            print("error")
    return JsonResponse({"YUPP":"GOTT"})


