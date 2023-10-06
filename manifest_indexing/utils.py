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
    """Generate a random string of fixed length """

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))


def download_file(url, filename):
    """
    Download data from url and save the content to filename
    """
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)


def write_csv(filename, files, fieldnames=None):
    """
    write to csv file

    Args:
        filename(str): file name
        files(list(dict)): list of file info
        [
            {
                "GUID": "guid_example",
                "filename": "example",
                "size": 100,
                "acl": "['open']",
                "md5": "md5_hash",
            },
        ]
        fieldnames(list(str)): list of column names

    Returns:
        filename(str): file name
    """

    if not files:
        return None
    fieldnames = fieldnames or files[0].keys()
    with open(filename, mode="w") as outfile:
        writer = csv.DictWriter(outfile, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()

        for f in files:
            writer.writerow(f)

    return filename


def upload_file(
    file_name,
    bucket,
    object_name=None,
    aws_access_key_id=None,
    aws_secret_access_key=None,
    config=Config(signature_version='s3v4'),
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
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :aws_access_key_id: string
    :aws_secret_access_key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
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
