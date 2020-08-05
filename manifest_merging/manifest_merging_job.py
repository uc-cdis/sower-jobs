"""
Module for bucket manifest merging using sower-jobs
"""

import os
import sys
import json
import logging
import boto3

from gen3.tools.indexing import merge_bucket_manifests

from settings import JOB_REQUIRES
from utils import (
    check_user_permission,
    detect_delimiter,
    upload_file_to_s3_and_generate_presigned_url,
)

LOG_FILE = "/manifest_merging.log"
INPUT_MANIFESTS_DIRECTORY = "/input_manifests"
OUTPUT_MANIFEST = "/output_manifest.txt"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    input_data_json = json.loads(os.environ["INPUT_DATA"])
    access_token = os.environ["ACCESS_TOKEN"]

    with open("/creds.json") as creds_file:
        job_name = "index-object-manifest"
        creds = json.load(creds_file).get(job_name, {})
        if not creds:
            logging.warning(
                f"No configuration found for '{job_name}' job. "
                "Attempting to continue anyway..."
            )

    # Only use provided authz requirement if resources are not empty
    access_authz_requirement = JOB_REQUIRES
    if creds.get("job_requires", {}).get("job_access_req"):
        access_authz_requirement = creds.get("job_requires")

    # check if user has sower and indexing policies
    is_allowed, message = check_user_permission(access_token, access_authz_requirement)
    if not is_allowed:
        logging.error(f"[out]: {message['message']}")
        sys.exit()

    os.mkdir(INPUT_MANIFESTS_DIRECTORY)
    s3 = boto3.client("s3")
    for i, url in enumerate(input_data_json["URLS"]):
        s3_bucket, s3_object = url.replace("s3://", "").split("/", 1)
        local_file_path = os.path.join(INPUT_MANIFESTS_DIRECTORY, f"manifest{i}.txt")

        logging.info(f"[out] downloading {url} to {local_file_path}")
        s3.download_file(s3_bucket, s3_object, local_file_path)

    merge_bucket_manifests(
        directory=INPUT_MANIFESTS_DIRECTORY,
        output_manifest_file_delimiter=detect_delimiter(local_file_path),
        output_manifest=OUTPUT_MANIFEST,
    )

    output_s3_bucket = creds["bucket"]
    log_file_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        output_s3_bucket, LOG_FILE
    )
    output_manifest_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        output_s3_bucket, OUTPUT_MANIFEST
    )

    logging.info(f"[out] {log_file_presigned_url} {output_manifest_presigned_url}")
