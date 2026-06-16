import json
from abc import ABC
from datetime import datetime

import boto3
import requests
from botocore.config import Config
from gen3cirrus import AwsService


class StorageClient(ABC):
    def upload_json_and_get_presigned_url(self, result):
        raise NotImplementedError


class S3StorageClient(StorageClient):
    def __init__(self, creds):
        for k in ["bucket_name", "aws_access_key_id", "aws_secret_access_key"]:
            assert creds.get(k), f"Missing key '{k}'"

        bucket_name = creds["bucket_name"]
        aws_access_key_id = creds["aws_access_key_id"]
        aws_secret_access_key = creds["aws_secret_access_key"]

        self.bucket_name = bucket_name
        client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        self.aws = AwsService(client)

    def upload_json_and_get_presigned_url(self, result):
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        filename = f"list_items-export_{timestamp}.json"
        upload_url = self.aws.upload_presigned_url(
            self.bucket_name, filename, expiration=3600
        )
        resp = requests.put(
            upload_url,
            data=json.dumps(result).encode("utf-8"),
        )

        resp.raise_for_status()

        return self.aws.download_presigned_url(
            self.bucket_name,
            filename,
            expiration=3600,
        )
