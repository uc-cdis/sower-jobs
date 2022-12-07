"""
See this repo's README file for details.
"""


from datetime import datetime
import json
import logging
import os
import sys
import traceback

from gen3 import object, metadata, auth


logging.basicConfig(filename="metadata_delete_expired_objects.log", level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def is_object_expired(metadata, now):
    try:
        expiration = float(metadata["_expires_at"])
    except ValueError:
        return False
    return expiration < now


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
    assert "hostname" in config, f"'hostname' is not set in configuration"

    # do not use `datetime.utcnow()` or the timestamp will be wrong, `timestamp()` already converts to UTC
    now = datetime.now().timestamp()
    logging.info(f"Deleting objects with an `_expires_at` timestamp earlier than {now}")

    _auth = auth.Gen3Auth(
        endpoint=config["hostname"],
        client_credentials=(config["oidc_client_id"], config["oidc_client_secret"]),
    )
    mds_handle = metadata.Gen3Metadata(_auth)
    object_api = object.Gen3Object(_auth)

    logging.info("Querying Metadata Service objects...")
    LIMIT_SIZE = 2000
    offset_position = 0
    response_dict = mds_handle.query(
        query="_expires_at=*", return_full_metadata=True, limit=LIMIT_SIZE
    )

    if type(response_dict) is not dict:
        raise Exception(
            f"Job Failed. Expected a dict but got a {type(response_dict)}: {response_dict}"
        )

    guid_list = [
        guid
        for guid, metadata in response_dict.items()
        if is_object_expired(metadata, now)
    ]
    while len(response_dict) == LIMIT_SIZE:
        offset_position += LIMIT_SIZE
        response_dict = mds_handle.query(
            query="_expires_at=*",
            return_full_metadata=True,
            limit=LIMIT_SIZE,
            offset=offset_position,
        )
        guid_list += [
            guid
            for guid, metadata in response_dict.items()
            if is_object_expired(metadata, now)
        ]
    logging.info(
        f"Found {len(response_dict)} objects with an expiration, of which {len(guid_list)} are expired"
    )

    logging.info("Deleting expired objects...")
    exception_counter, delete_counter = 0, 0
    for guid in guid_list:
        try:
            logging.info(f"Deleting object with guid -- {guid}")
            object_api.delete_object(guid=guid, delete_file_locations=True)
            delete_counter += 1
        except Exception:
            exception_counter += 1
            logging.error(f"Couldn't delete object with guid -- {guid}")
            traceback.print_exc()

    if exception_counter:
        raise Exception(
            f"Job Failed. Couldn't delete {exception_counter} objects. Check above logs for more info..."
        )
    logging.info(f"Job completed. Deleted {delete_counter} objects")


if __name__ == "__main__":
    main()
