"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import random
import string
import requests
import json
import logging
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


from gen3.tools.manifest_indexing import manifest_indexing


def randomString(stringLength=10):
    """Generate a random string of fixed length """

    letters = string.ascii_lowercase
    print("hello")
    return "".join(random.choice(letters) for i in range(stringLength))


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    # Upload the file
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client("s3")
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


def _download_file(url, filename):
    r = requests.get(url)
    with open(filename, "wb") as f:
        f.write(r.content)


def _upload_and_generate_presigned_url(bucket_name, filename, expiration=3600):
    """ Upload and generate presigned url"""

    now = datetime.now()

    if log_file and bucket_name:
        current_time = now.strftime("%m_%d_%y_%H:%M:%S")
        upload_file_key = "{}_{}.log".format(current_time, randomString(6))

        if upload_file(filename, bucket_name, upload_file_key):
            presigned_url = create_presigned_url(bucket_name, upload_file_key)
            return presigned_url

    return None


if __name__ == "__main__":
    hostname = os.environ["GEN3_HOSTNAME"]
    input_data = os.environ["INPUT_DATA"]

    input_data_json = json.loads(input_data)

    with open("/manifest-indexing-creds.json") as indexing_creds_file:
        indexing_creds = json.load(indexing_creds_file)

    auth = (
        indexing_creds.get("indexd_user", "gdcapi"),
        indexing_creds["indexd_password"],
    )

    filepath = "./manifest_tmp.tsv"
    _download_file(input_data_json["URL"], filepath)

    print("Start to index the manifest ...")

    host_url = input_data_json.get("host")
    if not host_url:
        host_url = "https://{}/index".format(hostname)

    log_file, output_manifest = manifest_indexing(
        filepath,
        host_url,
        input_data_json.get("thread_nums", 1),
        auth,
        input_data_json.get("prefix"),
        input_data_json.get("replace_urls"),
    )

    log_file_presigned_url = (
        _upload_and_generate_presigned_url(indexing_creds.get("bucket"), log_file)
        if log_file
        else None
    )

    output_manifest_presigned_url = (
        _upload_and_generate_presigned_url(
            indexing_creds.get("bucket"), output_manifest
        )
        if output_manifest
        else None
    )

    print("[out] {} {}".format(log_file_presigned_url, output_manifest_presigned_url))
