"""
This job requires Metadata Service >= 1.7.0 or 2022.06 and the Gen3 SDK >= 4.16.0.

It also requires providing the CLIENT_ID and CLIENT_SECRET environment variables:
credentials for an OIDC client with the "client_credentials" grant and "delete" access
in Metadata Service and Fence.
"""


import json
import logging
import os
import sys
from time import time
import traceback

from gen3 import object, metadata, auth


logging.basicConfig(filename="metadata_delete_expired_objects.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def main():
    logging.info("Initializing metadata_delete_expired_objects_job...")

    config_file_path = os.environ.get("CONFIG_PATH", "/mnt/config.json")
    if not os.path.exists(config_file_path):
        raise Exception(f"Configuration file not found at '{config_file_path}'")
    with open(config_file_path, "r") as f:
        config = json.load(f)
    assert "oidc_client_id" in config, f"'oidc_client_id' is not set in configuration"
    assert (
        "oidc_client_secret" in config
    ), f"'oidc_client_secret' is not set in configuration"
    assert "endpoint" in config, f"'endpoint' is not set in configuration"

    _auth = auth.Gen3Auth(
        endpoint=config["endpoint"],
        client_credentials=(config["oidc_client_id"], config["oidc_client_secret"]),
    )
    mds_handle = metadata.Gen3Metadata(_auth)
    object_api = object.Gen3Object(_auth)

    logging.info("Querying Metadata Service objects...")
    LIMIT_SIZE = 2000
    offset_position = 0
    response_dict = mds_handle.query(
        query="date_to_delete=*", return_full_metadata=True, limit=LIMIT_SIZE
    )

    if type(response_dict) is not dict:
        raise Exception(
            f"Job Failed. Expected a dict but got a {type(response_dict)}: {response_dict}"
        )

    guid_list = [
        record["guid"]
        for record in response_dict.values()
        if record["date_to_delete"] < time()
    ]
    while len(response_dict) == LIMIT_SIZE:
        offset_position += LIMIT_SIZE
        response_dict = mds_handle.query(
            query="date_to_delete=*",
            return_full_metadata=True,
            limit=LIMIT_SIZE,
            offset=offset_position,
        )
        guid_list += [
            record["guid"]
            for record in response_dict.values()
            if record["date_to_delete"] < time()
        ]
    logging.info(
        f"Found {len(response_dict)} objects with an expiration, of which {len(guid_list)} are expired"
    )

    logging.info("Deleting expired objects...")
    exception_counter, delete_counter = 0, 0
    for obj in guid_list:
        try:
            logging.info(f"Deleting object with guid -- {obj['guid']}")
            object_api.delete_object(guid=obj["guid"], delete_file_locations=True)
            delete_counter += 1
        except Exception as ex:
            exception_counter += 1
            logging.error(f"Couldn't delete object with guid -- {obj['guid']}")
            traceback.print_exc()

    if exception_counter:
        raise Exception(
            f"Job Failed. Couldn't delete {exception_counter} objects. Check above logs for more info..."
        )
    logging.info(f"Job completed. Deleted {delete_counter} objects")


if __name__ == "__main__":
    main()
