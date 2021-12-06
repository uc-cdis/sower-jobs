import requests
import json


class TemporaryAPIKey:
    file_name = "credentials.json"

    def __init__(self, token, hostname):
        self.token = token
        self.hostname = hostname
        self.api_key_id = None

    def __enter__(self):
        api_key_req = requests.post(
            f"https://{self.hostname}/user/credentials/api",
            headers={"Authorization": f"bearer {self.token}"},
        )
        api_key_req.raise_for_status()
        api_key = api_key_req.json()
        self.api_key_id = api_key["key_id"]

        with open(self.file_name, "w+") as f:
            f.write(json.dumps(api_key))

    def __exit__(self, exc_type, exc_val, exc_tb):
        requests.delete(
            f"https://{self.hostname}/user/credentials/api/{self.api_key_id}",
            headers={"Authorization": f"bearer {self.token}"},
        )
