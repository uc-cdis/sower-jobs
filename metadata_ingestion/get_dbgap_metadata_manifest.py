"""
Module for metadata ingestion actions using sower job dispatcher

Example input:

{
    "phsid_list": "phs000956 phs000920",
    "indexing_manifest_url": "indexing_manifest.csv",
    "manifests_mapping_config": {
        "guid_column_name": "guid",
        "row_column_name": "submitted_sample_id",
        "indexing_manifest_column_name": "urls",
    },
    "partial_match_or_exact_match": "partial_match",
}
"""
import os
import sys
import json
import logging

from gen3.tools import metadata
from gen3.tools.metadata.ingest_manifest import manifest_row_parsers

from gen3.tools.merge import (
    merge_guids_into_metadata,
    manifest_row_parsers,
    manifests_mapping_config,
    get_guids_for_manifest_row_partial_match,
)

from settings import JOB_REQUIRES
from utils import (
    download_file,
    check_user_permission,
    upload_file_to_s3_and_generate_presigned_url,
)

logging.basicConfig(filename="manifest_merge.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

INPUT_DATA = os.environ.get("INPUT_DATA")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")


def main():
    with open("/creds.json") as creds_file:
        job_name = "get-dbgap-metadata"
        creds = json.load(creds_file).get(job_name, {})
        if not creds:
            logging.warning(
                f"No configuration found for '{job_name}' job. "
                "Attempting to continue anyway..."
            )

    # Only use provided authz requirement if it's not empty
    access_authz_requirement = JOB_REQUIRES
    if creds.get("job_requires"):
        access_authz_requirement = creds.get("job_requires")

    # check if user has sower and ingestion policies
    is_allowed, message = check_user_permission(ACCESS_TOKEN, access_authz_requirement)
    if not is_allowed:
        print("[out]: {}".format(message["message"]))
        sys.exit()

    input_data_json = json.loads(INPUT_DATA)

    os.system(
        f"python ./dbgap-extract/dbgap_extract.py --study_accession_list "
        f"{input_data_json['phsid_list']} --output_filename metadata_manifest.tsv "
        "--expand_sra_details"
    )

    if "." in input_data_json["indexing_manifest_url"]:
        indexing_file_ext = input_data_json["indexing_manifest_url"].split(".")[-1]
    else:
        indexing_file_ext = "tsv"

    indexing_manifest = "indexing_manifest." + indexing_file_ext
    metadata_manifest = "metadata_manifest.tsv"

    download_file(input_data_json["indexing_manifest_url"], indexing_manifest)

    # what column to use as the final GUID for metadata (this MUST exist in the
    # indexing file)
    manifests_mapping_config["guid_column_name"] = input_data_json.get(
        "manifests_mapping_config", {}
    ).get("guid_column_name", "guid")

    # what column from the "metadata file" to use for mapping
    manifests_mapping_config["row_column_name"] = input_data_json.get(
        "manifests_mapping_config", {}
    ).get("row_column_name", "submitted_sample_id")

    # this configuration tells the function to use the "urls" column
    # from the "indexing file" to map to the metadata column configured above
    # (for partial matching the metdata data column to this column )
    manifests_mapping_config["indexing_manifest_column_name"] = input_data_json.get(
        "manifests_mapping_config", {}
    ).get("indexing_manifest_column_name", "urls")

    if input_data_json.get("partial_match_or_exact_match", "") == "partial_match":
        # by default, the functions for parsing the manifests and rows assumes a 1:1
        # mapping. There is an additional function provided for partial string matching
        # which we can use here.
        manifest_row_parsers[
            "guids_for_manifest_row"
        ] = get_guids_for_manifest_row_partial_match

    output_filename = "merged_metadata_manifest.tsv"

    merge_guids_into_metadata(
        indexing_manifest=indexing_manifest,
        metadata_manifest=metadata_manifest,
        output_filename=output_filename,
        manifests_mapping_config=manifests_mapping_config,
        manifest_row_parsers=manifest_row_parsers,
    )

    aws_access_key_id = creds.get("aws_access_key_id")
    aws_secret_access_key = creds.get("aws_secret_access_key")

    log_file_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        creds.get("bucket"),
        "manifest_merge.log",
        aws_access_key_id,
        aws_secret_access_key,
    )
    output_manifest_presigned_url = upload_file_to_s3_and_generate_presigned_url(
        creds.get("bucket"), output_filename, aws_access_key_id, aws_secret_access_key
    )

    print("[out] {} {}".format(log_file_presigned_url, output_manifest_presigned_url))


if __name__ == "__main__":
    main()
