"""
Module for metadata ingestion actions using sower job dispatcher
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
from utils import download_file, check_user_permission

logging.basicConfig(filename="manifest_ingestion.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

HOSTNAME = os.environ["GEN3_HOSTNAME"]
INPUT_DATA = os.environ["INPUT_DATA"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

# a file containing a "guid" column and additional, arbitrary columns to populate
# into the metadata service
MANIFEST = "metadata_manifest.tsv"


def main():
    # check if user has sower and ingestion policies
    is_allowed, message = check_user_permission(ACCESS_TOKEN, JOB_REQUIRES)
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


if __name__ == "__main__":
    main()
