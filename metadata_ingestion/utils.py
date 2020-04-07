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
