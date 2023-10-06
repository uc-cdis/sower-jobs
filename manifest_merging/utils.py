import csv
import random
import requests
from datetime import datetime
import string
import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config


def randomString(stringLength=10):
    """
    Generate a random string of fixed length

    Arg:
        stringLength(str): the desired length of the random string to generate

    Returns:
        str: the generated random string
    """

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


def upload_file(
    file_name,
    bucket,
    object_name=None,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    config=Config(signature_version='s3v4'),
):
    """
    Upload a file to an S3 bucket

    Args:
        file_name(str): file to upload
        bucket(str): bucket to upload to
        object_name(str): S3 object name. if not specified then file_name is used
        aws_access_key_id(str): aws access key id
        aws_secret_access_key(str): aws secret access key

    Returns:
        bool: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    if aws_access_key_id and aws_secret_access_key:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=config
        )
    else:
        s3_client = boto3.client("s3", config=config)

    try:
        msg = f"upload_file {file_name} in {bucket}, object: {object_name}"
        logging.info(msg)
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
    config=Config(signature_version='s3v4'),
):
    """
    Generate a presigned URL to share an S3 object

    Args:
        bucket_name(str): the bucket name
        object_name(str): S3 object name
        aws_access_key_id(str): aws access key id
        aws_secret_access_key(str): aws secret access key
        expiration(int): time in seconds for the presigned URL to remain valid

    Returns:
        str: presigned URL as string if successful. if error, returns None
    """
    # Generate a presigned URL for the S3 object
    if aws_access_key_id and aws_secret_access_key:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=config
        )
    else:
        s3_client = boto3.client("s3", config=config)

    try:
        msg = (
            f"generate_presigned_url {object_name} in {bucket_name}, exp: {expiration}"
        )
        logging.info(msg)
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
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
    """
    Upload and generate presigned url

    Args:
        bucket_name(str): the bucket name
        filename(str): the input file needs to be uploaded
        aws_access_key_id(str): aws access key id
        aws_secret_access_key(str): aws secret access key
        expiration(int): expiration time

    Returns:
        str: presigned url
    """

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


def check_user_permission(access_token, job_requires):
    """
    Check if user has permission to run the job or not

    Args:
        access_token(str): the access token
        job_requires(dict): requirements so that job can run
            {
                "arborist_url": "http://arborist-service",
                "job_access_req": (
                    [
                        {"resource": "/sower", "action": {"service": "job", "method": "access"}},
                        {"resource": "/programs", "action": {"service": "indexd", "method": "write"}},
                    ],
                )
            }
    Returns:
        bool: if user has permission to run the job or not
        dict: a message log
    """

    params = {
        "user": {"token": access_token},
        "requests": job_requires["job_access_req"],
    }
    response = requests.post(
        "{}/auth/request".format(job_requires["arborist_url"].strip("/")),
        headers={"content-type": "application/json"},
        json=params,
    )
    if response.status_code != 200:
        return (
            False,
            {"message": "Can not run the job. Detail {}".format(response.json())},
        )

    elif not response.json()["auth"]:
        return (False, {"message": "User does not have privilege to run the job"})
    else:
        return True, {"message": "OK"}


def detect_delimiter(dsv_filename):
    """
    Detect and return delimiter used in dsv_filename

    Args:
        dsv_filename(str): path to the delimiter-separated value file whose
        delimiter is to be detected

    Returns:
        str: the detected delimiter
    """
    with open(dsv_filename) as dsv_file:
        dialect = csv.Sniffer().sniff(dsv_file.readline())
    return dialect.delimiter
