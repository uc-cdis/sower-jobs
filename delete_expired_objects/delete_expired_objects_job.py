from time import time
import traceback
from gen3 import object, metadata, auth

"""
Note: This job requires Metadata service to be above version 1.7.0 or 2022.06
"""


def main():
    auth = auth.Gen3Auth(refresh_file="/mnt/api-profile-credentials.json")
    mds_handle = metadata.Gen3Metadata(auth)

    print("Initializing delete_expired_objects_job...")

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
    object_api = object.Gen3Object(auth)

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
