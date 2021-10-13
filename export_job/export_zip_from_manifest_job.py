import aiohttp
import asyncio
import json
import os
import shutil
from urllib.parse import quote_plus
from gen3.tools.download.drs_download import (
    # describe_access_to_files_in_workspace_manifest,
    download_files_in_workspace_manifest,
    list_files_in_workspace_manifest,
)
from gen3.auth import Gen3Auth
import requests
import boto3

from temporary_api_key import TemporaryAPIKey


CHUNK_SIZE = 10
MANIFEST_FILENAME = "manifest.json"
EXPORT_DIR = "export"
OUTPUT_PREFIX = "[out] "
MAX_DOWNLOAD_SIZE = 250000000
DEFAULT_ERROR_MESSAGE = (
    "Unable to complete this download. Please try again later, or use the Gen3 client."
)


async def build_manifest_from_study_ids(hostname, token, study_ids):
    """
    build a manifest from a list of metadata guids representing study ids
    dumps result to gen3-sdk compatible manifest file
    """
    ongoing_requests = []
    study_metadata = []

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

    manifest = []
    for study in study_metadata:
        if not study["__manifest"]:
            print(f"Study {study} is missing __manifest entry. Skipping.")
        else:
            manifest += study["__manifest"]

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
        # list_files_in_workspace_manifest(MANIFEST_FILENAME)
        describe_access_to_files_in_workspace_manifest(
            hostname, auth, MANIFEST_FILENAME
        )
        download_files_in_workspace_manifest(
            hostname, auth, MANIFEST_FILENAME, EXPORT_DIR
        )
        shutil.make_archive(EXPORT_DIR, "zip", EXPORT_DIR)


def upload_export_to_s3(s3_credentials, username):
    """
    uploads the local zip export to s3 and returns a presigned url, expires after 1 hour
    """
    bucket_name = s3_credentials["bucket_name"]
    aws_access_key_id = s3_credentials["aws_access_key_id"]
    aws_secret_access_key = s3_credentials["aws_secret_access_key"]

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

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
        input_data = json.loads(os.environ["INPUT_DATA"])
    except Exception as e:
        print(f"Unable to parse input_data {repr(e)}")
        fail()

    study_ids = input_data["study_ids"]
    if not study_ids:
        print("Missing input parameter 'study_ids'")
        fail("No studies provided. Please select some studies and try again.")

    try:
        with open("/batch-export-creds.json") as creds_file:
            s3_credentials = json.load(creds_file)
    except:
        print("S3 is misconfigured for this job.")
        fail()

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
            build_manifest_from_study_ids(hostname, access_token, study_ids)
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
        presigned_url = upload_export_to_s3(s3_credentials, username)
    except Exception as e:
        print(f"Export to s3 failed {repr(e)}")
        fail()

    # success
    # sower /status will show completed
    # sower /output will return { "output": presigned_url }
    print(f"{OUTPUT_PREFIX}{presigned_url}")
