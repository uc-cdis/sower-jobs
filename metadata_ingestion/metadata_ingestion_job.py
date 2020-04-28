"""
Module for metadata ingestion actions using sower job dispatcher

Example input:

{
    "URL": "metadata_manifest.tsv",
    "metadata_source": "dbgap",
    "host": "https://example-commons.com/"
}
"""
import os
import sys
import json
import logging
import asyncio

from gen3.auth import Gen3Auth
from gen3.tools import metadata
from gen3.tools.metadata.ingest_manifest import manifest_row_parsers

from settings import JOB_REQUIRES
from utils import (
    download_file,
    check_user_permission,
    upload_file_to_s3_and_generate_presigned_url,
)

logging.basicConfig(filename="manifest_ingestion.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

HOSTNAME = os.environ["GEN3_HOSTNAME"]
INPUT_DATA = os.environ["INPUT_DATA"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

# a file containing a "guid" column and additional, arbitrary columns to populate
# into the metadata service
MANIFEST = "metadata_manifest.tsv"


def main():
    with open("/creds.json") as creds_file:
        job_name = "ingest-metadata-manifest"
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

    # check if user has sower and ingestion policies
    is_allowed, message = check_user_permission(ACCESS_TOKEN, access_authz_requirement)
    if not is_allowed:
        print("[out]: {}".format(message["message"]))
        sys.exit()

    input_data_json = json.loads(INPUT_DATA)

    download_file(input_data_json["URL"], MANIFEST)

    commons_host_url = input_data_json.get("host")
    if not commons_host_url:
        commons_host_url = "https://{}/".format(HOSTNAME)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # use available access token instead of attempting refresh
    # NOTE: This means this will only continue so long as the access
    #       token isn't expired, which defaults to 20 minutes.
    auth = Gen3Auth(commons_host_url, refresh_token=ACCESS_TOKEN)
    auth._access_token = ACCESS_TOKEN

    loop.run_until_complete(
        metadata.async_ingest_metadata_manifest(
            commons_host_url,
            manifest_file=MANIFEST,
            metadata_source=input_data_json["metadata_source"],
            auth=auth,
        )
    )

    log_file_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        creds.get("bucket"), "manifest_ingestion.log"
    )

    print("[out] {}".format(log_file_presigned_url))


if __name__ == "__main__":
    main()
