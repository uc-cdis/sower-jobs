import json
import os
import shutil

import aiohttp
import asyncio
import boto3
from botocore.config import Config
from gen3.auth import Gen3Auth
from gen3.tools.download.drs_download import (
    list_access_in_drs_manifest,
    download_files_in_drs_manifest,
    list_files_in_drs_manifest,
)
from gen3.tools.download.external_file_download import download_files_from_metadata
from heal.harvard_downloads import get_harvard_dataverse_files
from heal.qdr_downloads import get_syracuse_qdr_files
import requests
from urllib.parse import quote_plus

from temporary_api_key import TemporaryAPIKey


CHUNK_SIZE = 10
MANIFEST_FILENAME = "manifest.json"
MANIFEST_FILENAME_EXTERNAL_FILES = "manifest_external_files.json"
EXPORT_DIR = "export"
OUTPUT_PREFIX = "[out] "
MAX_DOWNLOAD_SIZE = 250000000
DEFAULT_ERROR_MESSAGE = (
    "Unable to complete this download. Please try again later, or use the Gen3 client."
)


def write_manifest_to_temp_file(manifest, is_external_files=False):
    print(
        f"Assembled {'manifest of external files' if is_external_files else 'manifest'} for download"
    )
    print(json.dumps(manifest, indent=2))
    download_size = sum(file.get("file_size", 0) for file in manifest)
    if download_size > MAX_DOWNLOAD_SIZE:
        fail(
            f"The selected studies contain {download_size / 1000000} MB of data, "
            "which exceeds the download limit of 250 MB. "
            "Please deselect some studies and try again, or use the Gen3 client."
        )
    temp_manifest_file_to_write = (
        MANIFEST_FILENAME_EXTERNAL_FILES if is_external_files else MANIFEST_FILENAME
    )
    with open(temp_manifest_file_to_write, "w") as f:
        json.dump(manifest, f)


async def build_manifests(
    hostname, token, study_ids, file_manifest, external_file_metadata
):
    """
    build a manifest from a list of metadata GUIDs representing study ids
    if supplied with a file manifest, incorporate it in the final manifest file
    dumps result to gen3-sdk compatible manifest file
    """
    ongoing_requests = []
    study_metadata = []
    manifest = []
    manifest_external_files = []
    if file_manifest:
        print("Got file manifest from input")
        print(json.dumps(file_manifest, indent=2))
        manifest = file_manifest
    if external_file_metadata:
        print("Got external_file_metadata from input")
        print(json.dumps(external_file_metadata, indent=2))
        manifest_external_files = external_file_metadata

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
        if (
            not study["gen3_discovery"]["__manifest"]
            and not study["gen3_discovery"]["external_file_metadata"]
        ):
            print(
                f"Study {study} is missing '__manifest' and 'external_file_metadata'. Skipping."
            )
        else:
            if study["gen3_discovery"].get("__manifest"):
                print(
                    f'Study {study["gen3_discovery"].get("_hdp_uid")} has __manifest entry'
                )
                manifest += study["gen3_discovery"]["__manifest"]
            if study["gen3_discovery"].get("external_file_metadata"):
                print(
                    f'Study {study["gen3_discovery"].get("_hdp_uid")} has external_file_metadata'
                )
                manifest_external_files += study["gen3_discovery"][
                    "external_file_metadata"
                ]

    write_manifest_to_temp_file(manifest)
    write_manifest_to_temp_file(manifest_external_files, is_external_files=True)


def download_files(access_token, hostname, output_dir=EXPORT_DIR):
    """
    download the files described by the local manifest and export them to a zip
    """
    retrievers = {
        "QDR": get_syracuse_qdr_files,
        "Dataverse": get_harvard_dataverse_files,
    }

    with TemporaryAPIKey(token=access_token, hostname=hostname):
        auth = Gen3Auth(refresh_file=TemporaryAPIKey.file_name)

        # internal
        list_files_in_drs_manifest(hostname, auth, MANIFEST_FILENAME)
        list_access_in_drs_manifest(hostname, auth, MANIFEST_FILENAME)
        download_files_in_drs_manifest(hostname, auth, MANIFEST_FILENAME, output_dir)

        # external
        with open(MANIFEST_FILENAME_EXTERNAL_FILES, "r") as json_file:
            external_file_metadata = json.load(json_file)
        if len(external_file_metadata) > 0:
            download_status = download_files_from_metadata(
                hostname=hostname,
                auth=auth,
                external_file_metadata=external_file_metadata,
                retrievers=retrievers,
                download_path=output_dir,
            )
            print(f"External file download status '{download_status}'")
        else:
            print("No data in manifest file for external files - skipping")


def download_files_from_file_metadata(file_metadata, access_token, hostname):
    for folder_key, file_manifest_dict in file_metadata.items():
        has_item_to_download = False
        if "file_manifest" in file_manifest_dict:
            write_manifest_to_temp_file(file_manifest_dict.file_manifest)
            has_item_to_download = True
        if "external_file_metadata" in file_manifest_dict:
            write_manifest_to_temp_file(
                file_manifest_dict.external_file_metadata, is_external_files=True
            )
            has_item_to_download = True
        if has_item_to_download:
            download_files(
                access_token, hostname, output_dir=f"{EXPORT_DIR}/{folder_key}"
            )


def upload_export_to_s3(bucket_name, username, filename=None):
    """
    Uploads the local zip export to S3 and returns a presigned URL, expires after 1 hour.
    """

    s3_client = boto3.client("s3", config=Config(signature_version="s3v4"))
    export_key = f"{quote_plus(username)}-export.zip"
    content_disposition = (
        f'attachment; filename="{filename if filename else export_key}"'
    )

    s3_client.upload_file(
        Filename="export.zip",
        Bucket=bucket_name,
        Key=export_key,
        ExtraArgs={
            "ContentDisposition": content_disposition,
            "ContentType": "application/zip",
        },
    )

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket_name,
            "Key": export_key,
            "ResponseContentDisposition": content_disposition,
        },
        ExpiresIn=3600,
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

    file_metadata = input_data.get("file_metadata", None)
    if file_metadata:
        print("Got 'file_metadata' from input")

        try:
            download_files_from_file_metadata(file_metadata, access_token, hostname)
            shutil.make_archive(EXPORT_DIR, "zip", EXPORT_DIR)
        except Exception as e:
            print(f"Unable to download files from file metadata: {repr(e)}")
            fail()

    else:
        study_ids = input_data.get("study_ids", None)
        file_manifest = input_data.get("file_manifest", None)
        external_file_metadata = input_data.get("external_file_metadata", None)
        if not study_ids and not file_manifest and not external_file_metadata:
            print("Missing 'study_ids', 'file_manifest', and 'external_file_metadata'")
            fail(
                "No studies or files provided. Please select some studies or files and try again."
            )

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                build_manifests(
                    hostname,
                    access_token,
                    study_ids,
                    file_manifest,
                    external_file_metadata,
                )
            )
        except Exception as e:
            print(f"Unable to build a manifest from given study ids: {repr(e)}")
            fail()

        try:
            download_files(access_token, hostname)
            shutil.make_archive(EXPORT_DIR, "zip", EXPORT_DIR)
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
