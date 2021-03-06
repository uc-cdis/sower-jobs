"""
Module for indexing actions using sower job dispatcher

Attributes:
"""

import os
import sys
import json
import logging

from gen3.tools.indexing import index_object_manifest

from settings import JOB_REQUIRES
from utils import (
    write_csv,
    download_file,
    upload_file_to_s3_and_generate_presigned_url,
    check_user_permission,
)

logging.basicConfig(filename="manifest_indexing.log", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


if __name__ == "__main__":
    hostname = os.environ["GEN3_HOSTNAME"]
    input_data = os.environ["INPUT_DATA"]
    access_token = os.environ["ACCESS_TOKEN"]

    with open("/creds.json") as indexing_creds_file:
        job_name = "index-object-manifest"
        indexing_creds = json.load(indexing_creds_file).get(job_name, {})
        if not indexing_creds:
            logging.warning(
                f"No configuration found for '{job_name}' job. "
                "Attempting to continue anyway..."
            )

    # Only use provided authz requirement if resources are not empty
    access_authz_requirement = JOB_REQUIRES
    if indexing_creds.get("job_requires", {}).get("job_access_req"):
        access_authz_requirement = indexing_creds.get("job_requires")

    # check if user has sower and indexing policies
    is_allowed, message = check_user_permission(access_token, access_authz_requirement)
    if not is_allowed:
        print("[out]: {}".format(message["message"]))
        sys.exit()

    auth = (
        indexing_creds.get("indexd_user", "gdcapi"),
        indexing_creds["indexd_password"],
    )
    input_data_json = json.loads(input_data)

    filepath = "./manifest_tmp.tsv"
    download_file(input_data_json["URL"], filepath)

    print("Start to index the manifest ...")

    host_url = "http://revproxy-service/index/"

    files, headers = index_object_manifest(
        host_url,
        filepath,
        input_data_json.get("thread_nums", 1),
        auth,
        input_data_json.get("replace_urls", True),
        input_data_json.get("delimiter", "\t"),
    )

    output_manifest = "./output_manifest.tsv"
    write_csv(output_manifest, files, headers)

    log_file_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        indexing_creds["bucket"], "manifest_indexing.log"
    )

    output_manifest_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        indexing_creds["bucket"], output_manifest
    )

    print("[out] {} {}".format(log_file_presigned_url, output_manifest_presigned_url))
