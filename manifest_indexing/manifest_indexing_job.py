"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import json

from utils import (
    download_file,
    upload_file_to_s3_and_generate_presigned_url
)

from gen3.tools.manifest_indexing import manifest_indexing


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
    aws_access_key_id = indexing_creds.get("aws_access_key_id")
    aws_secret_access_key = indexing_creds.get("aws_secret_access_key")

    filepath = "./manifest_tmp.tsv"
    download_file(input_data_json["URL"], filepath)

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
        upload_file_to_s3_and_generate_presigned_url(
            indexing_creds["bucket"],
            log_file,
            aws_access_key_id,
            aws_secret_access_key,
        )
        if log_file
        else None
    )

    output_manifest_presigned_url = (
        upload_file_to_s3_and_generate_presigned_url(
            indexing_creds["bucket"],
            output_manifest,
            aws_access_key_id,
            aws_secret_access_key,
        )
        if output_manifest
        else None
    )

    print("[out] {} {}".format(log_file_presigned_url, output_manifest_presigned_url))
