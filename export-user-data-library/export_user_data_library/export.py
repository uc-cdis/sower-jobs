import asyncio
from abc import ABC, abstractmethod
from typing import Any

from gen3.file import Gen3File
from gen3.jobs import Gen3Jobs
from cdislogging import get_logger
from gen3.auth import Gen3Auth

from export_user_data_library.config import ConfigProvider

import requests

logger = get_logger(__name__)


class ListExporter:
    """
    Generates export information, including the method to retrieve the item, for each item in a list with an
    optionally filter for items within a list.
    """

    def __init__(self, config: ConfigProvider):
        self.access_token = config.get_access_token()
        self.auth = Gen3Auth(access_token=self.access_token)
        self.data_library = config.get_data_library_service()
        self.export_info = config.get_export_info()
        self.list_id = self.export_info.get("list_id")
        self.items = set(self.export_info.get("items", []))

    async def export(self):
        """
        Exports each item in the list, if requested.
        """
        list_items = self.get_list_from_data_library()
        result = []

        for name, item in list_items.items():
            if self.items and name not in self.items:
                logger.info(f"{name} is not in the provided items, skipping")
                continue
            exporter: ItemExporter = get_exporter(item["type"], self.auth)
            url = await exporter.export(name, item)
            item_export = {**item, **{"url": url, "guid": name}}
            result.append(item_export)

        return result

    def get_list_from_data_library(self):
        """
        Retrieves a list from the data library.
        """
        resp = requests.get(
            f"{self.data_library}/lists/{self.list_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        if not resp.ok:
            raise Exception(f"Export failed, cannot retrieve {self.list_id}")

        if "application/json" not in resp.headers.get("content-type"):
            raise Exception(
                f"Unexpected content-type response from data library, expected json got {resp.headers.get('content-type')}"
            )

        user_list = resp.json()

        # Extract items from the list response
        # The API response structure is: {"lists": {"<list_id>": {"items": {...}}}}
        # We need to extract just the items from this list
        if "lists" in user_list and self.list_id in user_list["lists"]:
            return user_list["lists"][self.list_id].get("items", {})

        return user_list


class ItemExporter(ABC):
    """
    Abstract base class representing the export operations for a list item
    """

    def __init__(self, auth: Gen3Auth):
        self.auth = auth

    @abstractmethod
    async def export(self, item_name: str, item_config: dict[str, Any]) -> str:
        raise NotImplementedError


class Gen3GraphQLItemExporter(ItemExporter):
    """
    Export class for the GraphQL export list item types.
    """

    def __init__(self, auth: Gen3Auth):
        super().__init__(auth)
        self.jobs = Gen3Jobs(auth_provider=auth)

    async def export(self, item_name: str, item_config: dict[str, Any]) -> str:
        return (
            await self.jobs.async_run_job_and_wait(
                "pelican",
                {"action": "export", "input": item_config["variables"]["filter"]},
            )
        ).get("output")


class Ga4ghDrsItemExporter(ItemExporter):
    """
    Export class for the DRS export list item types.
    """

    def __init__(self, auth: Gen3Auth):
        super().__init__(auth)
        self.file = Gen3File(auth_provider=auth)

    async def export(self, item_name: str, item_config: dict[str, Any]) -> str:
        return await asyncio.to_thread(self.file.get_presigned_url, item_name)


# Add new list item handlers here
EXPORTERS: dict[str, type[ItemExporter]] = {
    "Gen3GraphQL": Gen3GraphQLItemExporter,
    "GA4GH_DRS": Ga4ghDrsItemExporter,
}


def get_exporter(item_type: str, auth: Gen3Auth) -> ItemExporter:
    """
    Returns an instance of the export class for a given item type.
    """
    try:
        return EXPORTERS[item_type](auth)
    except KeyError as exc:
        raise ValueError(f"Unsupported export type: {item_type}") from exc
