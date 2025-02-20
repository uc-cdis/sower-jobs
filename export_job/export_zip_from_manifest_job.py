import aiohttp
import asyncio
import json
import os
import shutil
from urllib.parse import quote_plus
from gen3.tools.download.drs_download import (
    list_access_in_drs_manifest,
    download_files_in_drs_manifest,
    list_files_in_drs_manifest,
)
from gen3.auth import Gen3Auth
import requests
import boto3
from botocore.config import Config

from temporary_api_key import TemporaryAPIKey


CHUNK_SIZE = 10
MANIFEST_FILENAME = "manifest.json"
EXPORT_DIR = "export"
OUTPUT_PREFIX = "[out] "
MAX_DOWNLOAD_SIZE = 250000000
DEFAULT_ERROR_MESSAGE = (
    "Unable to complete this download. Please try again later, or use the Gen3 client."
)


async def build_manifest_from_study_ids(hostname, token, study_ids, file_manifest):
    """
    build a manifest from a list of metadata guids representing study ids
    if supplied with a file manifest, incorporate it in the final manifest file
    dumps result to gen3-sdk compatible manifest file
    """
    ongoing_requests = []
    study_metadata = []
    manifest = []
    if file_manifest:
        print("Got file manifest from input")
        print(json.dumps(file_manifest, indent=2))
        manifest = file_manifest

    if study_ids:
        print(f"Assembling manifest for study ids: {study_ids}")
        async with aiohttp.ClientSession() as client:
            for study_id in study_ids:
                ongoing_requests += [
                    client.get(
                        f"https://{hostname}/mds/aggregate/metadata/guid/{study_id}",
                        headers={"Authorization": f"bearer {token}"},
                    )
                ]
                if len(ongoing_requests) == CHUNK_SIZE:
                    study_metadata += await asyncio.gather(
                        *[req.json() for req in await asyncio.gather(*ongoing_requests)]
                    )

            study_metadata += await asyncio.gather(
                *[req.json() for req in await asyncio.gather(*ongoing_requests)]
            )

    for study in study_metadata:
        if not study["gen3_discovery"]["__manifest"]:
            print(
                f"Study {study} is missing __manifest entry in gen3_discovery. Skipping."
            )
        else:
            manifest += study["gen3_discovery"]["__manifest"]

    print("Assembled manifest for download")
    print(json.dumps(manifest, indent=2))
    download_size = sum(file.get("file_size", 0) for file in manifest)
    if download_size > MAX_DOWNLOAD_SIZE:
        fail(
            f"The selected studies contain {download_size / 1000000} MB of data, "
            "which exceeds the download limit of 250 MB. "
            "Please deselect some studies and try again, or use the Gen3 client."
        )

    with open(MANIFEST_FILENAME, "w+") as f:
        json.dump(manifest, f)


def download_files(access_token, hostname):
    """
    download the files described by the local manifest and export them to a zip
    """
    with TemporaryAPIKey(token=access_token, hostname=hostname):
        auth = Gen3Auth(refresh_file=TemporaryAPIKey.file_name)
        list_files_in_drs_manifest(hostname, auth, MANIFEST_FILENAME)
        list_access_in_drs_manifest(hostname, auth, MANIFEST_FILENAME)
        download_files_in_drs_manifest(hostname, auth, MANIFEST_FILENAME, EXPORT_DIR)
        shutil.make_archive(EXPORT_DIR, "zip", EXPORT_DIR)


def upload_export_to_s3(bucket_name, username):
    """
    Uploads the local zip export to S3 and returns a presigned URL, expires after 1 hour.
    """

    s3_client = boto3.client("s3", config=Config(signature_version='s3v4'))

    export_key = f"{quote_plus(username)}-export.zip"
    s3_client.upload_file("export.zip", bucket_name, export_key)

    url = s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket_name, "Key": export_key}, ExpiresIn=3600
    )

    return url


def fail(error_message=DEFAULT_ERROR_MESSAGE):
    """
    fail the job
    sower /status will show failure
    sower /output will show :error_message:
    """
    print(f"{OUTPUT_PREFIX}{error_message}")
    exit(1)


if __name__ == "__main__":
    access_token = os.environ["ACCESS_TOKEN"]
    hostname = os.environ["GEN3_HOSTNAME"]
    try:
        bucket_name = os.environ["BUCKET"]
    except Exception as e:
        print("Error: Environment variable 'BUCKET' is not set.")
        fail()
    try:
        input_data = json.loads(os.environ["INPUT_DATA"])
    except Exception as e:
        print(f"Unable to parse input_data {repr(e)}")
        fail()

    study_ids = input_data.get("study_ids", None)
    file_manifest = input_data.get("file_manifest", None)
    if not study_ids and not file_manifest:
        print("Both input parameter 'study_ids' and 'file_manifest' are missing")
        fail(
            "No studies or files provided. Please select some studies or files and try again."
        )

    try:
        username_req = requests.get(
            f"https://{hostname}/user/user",
            headers={"Authorization": f"bearer {access_token}"},
        )
        username_req.raise_for_status()
        username = username_req.json()["username"]
    except Exception as e:
        print(f"Unable to authorize user from access token -- {e}")
        fail("Unable to authorize user.")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            build_manifest_from_study_ids(
                hostname, access_token, study_ids, file_manifest
            )
        )
    except Exception as e:
        print(f"Unable to build a manifest from given study ids: {repr(e)}")
        fail()

    try:
        download_files(access_token, hostname)
    except Exception as e:
        print(f"Unable to download files: {repr(e)}")
        fail()

    try:
        presigned_url = upload_export_to_s3(bucket_name, username)
    except Exception as e:
        print(f"Export to s3 failed {repr(e)}")
        fail()

    # success
    # sower /status will show completed
    # sower /output will return { "output": presigned_url }
    print(f"{OUTPUT_PREFIX}{presigned_url}")
