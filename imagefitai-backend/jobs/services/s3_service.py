import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import uuid
import os


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    def generate_presigned_upload_url(self, file_name: str, content_type: str) -> dict:
        """Generate a presigned URL for uploading a file to S3."""
        # Create a unique key for the file
        file_extension = os.path.splitext(file_name)[1]
        s3_key = f"uploads/{uuid.uuid4()}{file_extension}"

        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type,
                },
                ExpiresIn=3600  # URL valid for 1 hour
            )
            return {
                'upload_url': presigned_url,
                's3_key': s3_key
            }
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def download_file(self, s3_key: str, local_path: str) -> str:
        """Download a file from S3 to local path."""
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return local_path
        except ClientError as e:
            raise Exception(f"Failed to download file: {str(e)}")

    def upload_file(self, local_path: str, s3_key: str) -> str:
        """Upload a file from local path to S3."""
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            return s3_key
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    def generate_presigned_download_url(self, s3_key: str) -> str:
        """Generate a presigned URL for downloading a file from S3."""
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                },
                ExpiresIn=3600  # URL valid for 1 hour
            )
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")