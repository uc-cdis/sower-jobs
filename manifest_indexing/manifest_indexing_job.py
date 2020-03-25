"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import sys
import json
import logging
import requests

from utils import write_csv, download_file, upload_file_to_s3_and_generate_presigned_url
from settings import ARBORIST_URL

from gen3.tools.indexing import index_object_manifest

logging.basicConfig(filename="manifest_indexing.log", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


if __name__ == "__main__":
    hostname = os.environ["GEN3_HOSTNAME"]
    input_data = os.environ["INPUT_DATA"]
    access_token = os.environ["ACCESS_TOKEN"]

    input_data_json = json.loads(input_data)

    # check if user has sower and indexing policies 
    response = requests.get("{}/auth/resources".format(ARBORIST_URL), headers={"Authorization": access_token})
    if response.status_code !=200:
        print("[out] can not run the job. Detail {}".format(response.json()))
    elif "/sower" not in response.json().get("resources", []) or "/indexing" not in response.json().get("resources", []):
        print("[out] user does not have privilege to run indexing job")
    else:
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

        files, headers = index_object_manifest(
            host_url,
            filepath,
            input_data_json.get("thread_nums", 1),
            auth,
            input_data_json.get("replace_urls"),
            input_data_json.get("delimiter", "\t"),
        )

        output_manifest = "./output_manifest.tsv"
        write_csv(output_manifest, files, headers)

        log_file_presigned_url = upload_file_to_s3_and_generate_presigned_url(
            indexing_creds["bucket"],
            "manifest_indexing.log",
            aws_access_key_id,
            aws_secret_access_key,
        )

        output_manifest_presigned_url = upload_file_to_s3_and_generate_presigned_url(
            indexing_creds["bucket"],
            output_manifest,
            aws_access_key_id,
            aws_secret_access_key,
        )

        print("[out] {} {}".format(log_file_presigned_url, output_manifest_presigned_url))
