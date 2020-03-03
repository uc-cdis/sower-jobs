import random
import requests
from datetime import datetime
import string
import logging
import boto3
from botocore.exceptions import ClientError


def randomString(stringLength=10):
    """Generate a random string of fixed length """

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))

def download_file(url, filename):
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)

def upload_file(
    file_name,
    bucket,
    object_name=None,
    aws_access_key_id=None,
    aws_secret_access_key=None,
):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :aws_access_key_id: string
    :aws_secret_access_key: string
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    # Upload the file
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def create_presigned_url(
    bucket_name,
    object_name,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    expiration=3600,
):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :aws_access_key_id: string
    :aws_secret_access_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        print(e)
        return None
    # The response contains the presigned URL
    return response

def upload_file_to_s3_and_generate_presigned_url(
    bucket_name,
    filename,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    expiration=3600,
):
    """ Upload and generate presigned url"""

    now = datetime.now()

    if filename and bucket_name:
        current_time = now.strftime("%m_%d_%y_%H:%M:%S")
        upload_file_key = "{}_{}.log".format(current_time, randomString(6))

        if upload_file(
            filename,
            bucket_name,
            upload_file_key,
            aws_access_key_id,
            aws_secret_access_key,
        ):
            presigned_url = create_presigned_url(
                bucket_name, upload_file_key, aws_access_key_id, aws_secret_access_key
            )
            return presigned_url

    return None
