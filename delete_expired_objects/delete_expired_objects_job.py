"""
This job requires Metadata Service >= 1.7.0 or 2022.06 and the Gen3 SDK >= 4.16.0.

It also requires providing the CLIENT_ID and CLIENT_SECRET environment variables:
credentials for an OIDC client with the "client_credentials" grant and "delete" access
in Metadata Service and Fence.
"""


import os
from time import time
import traceback

from gen3 import object, metadata, auth


def main():
    print("Initializing delete_expired_objects_job...")

    assert "CLIENT_ID" in os.environ, f"CLIENT_ID environment variable not set"
    assert "CLIENT_SECRET" in os.environ, f"CLIENT_SECRET environment variable not set"
    _auth = auth.Gen3Auth(
        client_credentials=(os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"])
    )
    mds_handle = metadata.Gen3Metadata(_auth)
    object_api = object.Gen3Object(_auth)

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

    exception_counter, delete_counter = 0, 0
    for obj in guid_list:
        try:
            print(f"Deleting object with guid -- {obj['guid']}")
            object_api.delete_object(guid=obj["guid"], delete_file_locations=True)
            delete_counter += 1
        except Exception as ex:
            exception_counter += 1
            print(f"Couldn't delete object with guid -- {obj['guid']}")
            traceback.print_exc()

    if exception_counter:
        raise Exception(
            f"Job Failed. Couldn't delete {exception_counter} objects. Check above logs for more info..."
        )
    print(f"Job completed. Deleted {delete_counter} objects...")


if __name__ == "__main__":
    main()
