import json
import os
from abc import ABC, abstractmethod
from cdislogging import get_logger

logger = get_logger(__name__)


class ConfigProvider(ABC):
    """
    Interface for retrieving configuration for the job.
    """

    @abstractmethod
    def get_access_token(self) -> str:
        """
        Returns an access token used to retrieve audit records from the audit-service
        """
        pass

    @abstractmethod
    def get_export_info(self) -> dict:
        """
        Returns the list_id and selected items.
        Example:
            {
                "list_id": "presigned_url",
                "items": [
                    "dg.TEST/some-uuid",
                    "dg.TEST/some-other-uuid"
                ]
            }
        """
        pass

    def get_data_library_service(self) -> str:
        """
        :return: the location of the gen3-user-data-library service
        """
        return "http://gen3-user-data-library-service"


class EnvConfigProvider(ConfigProvider):
    """
    Retrieves config information from environment variables, such as when the job is executed with sower.
    """

    def get_access_token(self) -> str:
        token = os.environ.get("ACCESS_TOKEN")
        if not token:
            raise ValueError("Missing ACCESS_TOKEN in environment.")
        return token

    def get_export_info(self) -> dict:
        input_data_str = os.environ.get("INPUT_DATA")
        if not input_data_str:
            raise ValueError("Missing INPUT_DATA in environment.")
        export_info = json.loads(input_data_str)

        if "list_id" not in export_info:
            raise ValueError("Missing list_id in INPUT_DATA")

        if not export_info.get("items"):
            logger.info("No items provided, exporting the whole list.")

        return export_info


class TesConfigProvider(ConfigProvider):
    """
    TODO: Add TES support
    """

    def get_access_token(self) -> str:
        raise NotImplementedError

    def get_export_info(self) -> dict:
        raise NotImplementedError
