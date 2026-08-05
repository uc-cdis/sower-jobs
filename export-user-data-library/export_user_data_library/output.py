import json
from abc import ABC, abstractmethod
from typing import Any


class OutputProvider(ABC):
    @abstractmethod
    def write(self, result: list[dict[str, Any]]):
        raise NotImplementedError


class JsonOutputProvider(OutputProvider):
    def write(self, result: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return result


class PresignedUrlOutputProvider(OutputProvider):
    def __init__(self, storage_client):
        self.storage_client = storage_client

    def write(self, result: list[dict[str, Any]]) -> str:

        url = self.storage_client.upload_json_and_get_presigned_url(
            result=result,
        )

        return url
