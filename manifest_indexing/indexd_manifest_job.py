"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import json
import asyncio
import requests

from gen3.tools import indexing

from utils import upload_file_to_s3_and_generate_presigned_url, check_user_permission

if __name__ == "__main__":
    hostname = os.environ["GEN3_HOSTNAME"]
    input_data = os.environ["INPUT_DATA"]
    access_token = os.environ["ACCESS_TOKEN"]

    input_data_json = json.loads(input_data)
    if not input_data_json:
        input_data_json = {}

    is_allowed, message = check_user_permission(access_token)
    if not is_allowed:
        print("[out]: {}".format(message["message"]))
    else:
        with open("/manifest-indexing-creds.json") as indexing_creds_file:
            indexing_creds = json.load(indexing_creds_file)

        aws_access_key_id = indexing_creds.get("aws_access_key_id")
        aws_secret_access_key = indexing_creds.get("aws_secret_access_key")

        print("Start to download manifest ...")

        common_url = input_data_json.get("host")
        if not common_url:
            common_url = "https://{}".format(hostname)

        num_process = input_data_json.get("num_processes", 1)
        max_concurrent_requests = input_data_json.get("max_concurrent_requests", 8)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            indexing.async_download_object_manifest(
                common_url,
                output_filename="object-manifest.csv",
                num_processes=num_process,
                max_concurrent_requests=max_concurrent_requests,
            )
        )

        output_manifest_presigned_url = upload_file_to_s3_and_generate_presigned_url(
            indexing_creds.get("bucket"),
            "object-manifest.csv",
            aws_access_key_id,
            aws_secret_access_key,
        )

        print("[out] {}".format(output_manifest_presigned_url))
