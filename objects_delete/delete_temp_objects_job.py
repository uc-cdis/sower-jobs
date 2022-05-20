from time import time
from gen3 import object, metadata, auth

auth = auth.Gen3Auth(refresh_file="/mnt/sai-credentials.json")
mds_handle = metadata.Gen3Metadata(auth)

print("Initializing delete_temp_objects_job...")
LIMIT_SIZE = 2
offset_position = 0
response_dict = mds_handle.query(
    query="date_to_delete=*", return_full_metadata=True, limit=LIMIT_SIZE
)
if type(response_dict) is dict:
    guid_list = list(response_dict.values())
    while len(response_dict) == LIMIT_SIZE:
        offset_position += LIMIT_SIZE
        response_dict = mds_handle.query(
            query="date_to_delete=*",
            return_full_metadata=True,
            limit=LIMIT_SIZE,
            offset=offset_position,
        )
        if response_dict:
            guid_list += list(response_dict.values())
    delete_list = [obj["guid"] for obj in guid_list if obj["date_to_delete"] < time()]
    object_api = object.Gen3Object(auth)
    for guid in delete_list:
        try:
            print(f"Deleting object with guid -- {guid}")
            object_api.delete_object(guid=guid)
        except Exception as ex:
            print(f"Couldn't delete object with guid -- {guid}\n{ex}")
print(f"Job completed. Deleted {len(delete_list)} objects...")
