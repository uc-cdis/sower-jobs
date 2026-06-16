import asyncio
import json
import os.path
from cdislogging import get_logger

from export_user_data_library.config import EnvConfigProvider
from export_user_data_library.export import ListExporter
from export_user_data_library.storage import S3StorageClient
from export_user_data_library.response_writer import SowerResponseWriter
from export_user_data_library.output import (
    PresignedUrlOutputProvider,
    JsonOutputProvider,
)

logger = get_logger(__name__)


async def main():
    # TODO Read output, response writer from config
    config = EnvConfigProvider()
    list_exporter = ListExporter(config=config)
    if os.path.isfile("/export-user-data-library-creds.json"):
        logger.info(
            "Bucket credentials provided, uploading results to S3. Output will be a presigned-url pointing to the results"
        )
        with open("/export-user-data-library-creds.json") as f:
            creds = json.load(f)
        storage_client = S3StorageClient(creds=creds)
        output_format = PresignedUrlOutputProvider(storage_client=storage_client)
    else:
        logger.info("No bucket creds provided, output result directly")
        output_format = JsonOutputProvider()

    response_writer = SowerResponseWriter()

    result = await list_exporter.export()
    url = await output_format.write(result)
    response_writer.write(url)


if __name__ == "__main__":
    asyncio.run(main())
