"""Upload report files to S3 and return presigned download URLs."""

from typing import Any

import boto3
from botocore.config import Config

from metrics_report.config import BucketConfig
from metrics_report.reports import Report

KEY_PREFIX = "metrics-report"
# Matches Sower's default pod TTL: `GET /job/output` stops working at about
# the same time the links expire.
URL_EXPIRES_IN_SECONDS = 3600


class ReportStorage:
    """Stores report files under `metrics-report/<run id>/<file name>`."""

    def __init__(self, s3_client: Any, bucket_name: str) -> None:
        self.s3_client = s3_client
        self.bucket_name = bucket_name

    @classmethod
    def from_config(cls, bucket: BucketConfig) -> "ReportStorage":
        """Create storage that writes with the keys from the credentials file."""
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=bucket.aws_access_key_id,
            aws_secret_access_key=bucket.aws_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        return cls(s3_client, bucket.name)

    def upload(self, run_id: str, report: Report) -> str:
        """
        Upload one report file.

        Each run uses its own `run_id`, so a re-run for the same month does not
        overwrite the earlier files.

        Args:
            run_id (str): Folder name for this run's files.
            report (Report): The file to upload.

        Returns:
            str: A presigned URL that downloads the file.

        Raises:
            botocore.exceptions.BotoCoreError: If the upload fails.
            botocore.exceptions.ClientError: If S3 rejects the upload.
        """
        key = f"{KEY_PREFIX}/{run_id}/{report.filename}"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=report.to_tsv(),
            ContentType="text/tab-separated-values",
        )
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=URL_EXPIRES_IN_SECONDS,
        )
