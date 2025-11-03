import boto3
import os

class SpacesHelper:

    def __init__(self, region='nyc3'):
        self.s3_client = boto3.client('s3',
                                      region_name=os.getenv('DO_SPACES_REGION', region),
                                      endpoint_url=f'https://{os.getenv('DO_SPACES_REGION', region)}.digitaloceanspaces.com',
                                      aws_access_key_id=os.getenv('DO_SPACES_KEY'),
                                      aws_secret_access_key=os.getenv('DO_SPACES_SECRET'))

    def upload_file(self, bucket_name, file_path, object_name, public=False, content_type=None):
        """
        Upload a file to the specified bucket.
        :param bucket_name:
        :param file_path:
        :param object_name:
        :param public: if True, set ACL to public-read (object will be publicly accessible)
        :param content_type: optional content type to set on the object
        :return: public URL (if bucket/object is public) or URL path (may be inaccessible if private)
        """
        try:
            # Build ExtraArgs only when needed
            extra_args = {}
            if public:
                extra_args['ACL'] = 'public-read'
            if content_type:
                extra_args['ContentType'] = content_type

            # boto3.upload_file accepts ExtraArgs parameter
            self.s3_client.upload_file(file_path, bucket_name, object_name, ExtraArgs=extra_args or None)

            # return public URL (note: accessibility depends on ACL/bucket policy)
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

    def generate_presigned_url(self, bucket_name, object_name, expires_in=3600):
        """
        Generate a presigned URL for temporary access to a private object.
        :param bucket_name:
        :param object_name:
        :param expires_in: seconds until expiry
        :return: presigned URL string
        """
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expires_in
            )
        except Exception as e:
            raise Exception(f"Error generating presigned URL: {e}")
