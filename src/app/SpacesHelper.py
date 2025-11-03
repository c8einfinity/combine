import boto3
import os

class SpacesHelper:

    def __init__(self, region='nyc3'):
        self.s3_client = boto3.client('s3',
                                      region_name=os.getenv('DO_SPACES_REGION', region),
                                      endpoint_url=f'https://{os.getenv('DO_SPACES_REGION', region)}.digitaloceanspaces.com',
                                      aws_access_key_id=os.getenv('DO_SPACES_KEY'),
                                      aws_secret_access_key=os.getenv('DO_SPACES_SECRET'))

    def upload_file(self, bucket_name, file_path, object_name):
        """
        Upload a file to the specified bucket.
        :param bucket_name:
        :param file_path:
        :param object_name:
        :return:
        """
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            # return public URL
            url = f"https://{bucket_name}.{os.getenv('DO_SPACES_REGION', 'nyc3')}.digitaloceanspaces.com/{object_name}"
            print(f"File uploaded to {url}")
            return url
        except Exception as e:
            raise Exception(f"Error uploading file: {e}")

    def download_file(self, bucket_name, object_name, file_path):
        """
        Download a file from the specified bucket.
        :param bucket_name:
        :param object_name:
        :param file_path:
        :return:
        """
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            return file_path
        except Exception as e:
            raise Exception(f"Error downloading file: {e}")

    def list_files(self, bucket_name):
        """
        List files in the specified bucket.
        :param bucket_name:
        :return:
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in response:
                return response['Contents']
            return []
        except Exception as e:
            raise Exception(f"Error listing files: {e}")

    def delete_file(self, bucket_name, object_name):
        """
        Delete a file from the specified bucket.
        :param bucket_name:
        :param object_name:
        :return:
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            return True
        except Exception as e:
            raise Exception(f"Error deleting file: {e}")
