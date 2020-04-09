import csv
import random
import requests
from datetime import datetime
import string
import logging
import boto3
from botocore.exceptions import ClientError


def download_file(url, filename):
    """
    Download data from url and save the content to filename
    """
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)


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
        return (False, {"message": "User does not have privilege to run indexing job"})
    else:
        return True, {"message": "OK"}


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
