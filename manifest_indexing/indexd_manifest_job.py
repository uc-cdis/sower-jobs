"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import json
import asyncio

from gen3.tools import indexing

from utils import (
    upload_file_to_s3_and_generate_presigned_url
)

if __name__ == "__main__":
    hostname = os.environ["GEN3_HOSTNAME"]
    input_data = os.environ["INPUT_DATA"]

    input_data_json = json.loads(input_data)

    with open("/manifest-indexing-creds.json") as indexing_creds_file:
        indexing_creds = json.load(indexing_creds_file)

    aws_access_key_id = indexing_creds.get("aws_access_key_id")
    aws_secret_access_key = indexing_creds.get("aws_secret_access_key")

    print("Start to download_manifest index the manifest ...")

    common_url = input_data_json.get("host")
    if not common_url:
        common_url = "https://{}".format(hostname)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        indexing.async_download_object_manifest(
            common_url,
            output_filename="object-manifest.csv",
            num_processes=8,
            max_concurrent_requests=24,
        )
    )
    
    output_manifest_presigned_url = (
        upload_file_to_s3_and_generate_presigned_url(
            indexing_creds.get("bucket"),
            "object-manifest.csv",
            aws_access_key_id,
            aws_secret_access_key,
        )
    )

    print("[out] {}".format(output_manifest_presigned_url))
