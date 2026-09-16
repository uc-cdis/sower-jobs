import pytest
from unittest.mock import Mock, AsyncMock, patch

from export_user_data_library.export import ListExporter


# Expected items that are reused across tests
EXPECTED_DRS_ITEM_1 = {
    "type": "GA4GH_DRS",
    "dataset_guid": "phs000007.v35.p16.c1",
    "name": "Item 1",
    "display_name": "Test Item 1",
    "description": "A test item",
    "guid": "dg.4503/item1",
    "signed_url": "http://presigned-url-1",
}

EXPECTED_DRS_ITEM_2 = {
    "type": "GA4GH_DRS",
    "dataset_guid": "phs000008.v36.p17.c2",
    "display_name": "Test Item 2",
    "guid": "dg.4503/item2",
    "signed_url": "http://presigned-url-2",
}

EXPECTED_GRAPHQL_ITEM_1 = {
    "type": "Gen3GraphQL",
    "name": "GraphQL Export 1",
    "schema_version": "1.0",
    "data": {
        "query": "{ project { code } }",
        "variables": {"filter": {"project": {"code": "TEST"}}},
    },
    "guid": "graphql-item-1",
    "signed_url": "http://job-output-1",
}

EXPECTED_GRAPHQL_ITEM_2 = {
    "type": "Gen3GraphQL",
    "name": "GraphQL Export 2",
    "schema_version": "1.0",
    "data": {
        "query": "{ subject { submitter_id } }",
        "variables": {"filter": {}},
    },
    "guid": "graphql-item-2",
    "signed_url": "http://job-output-2",
}


@pytest.mark.asyncio
async def test_list_exporter_ga4gh_drs_items(
    mock_config, mock_data_library_response, mock_gen3auth, mock_gen3file
):
    """
    Verify that ListExporter exports GA4GH_DRS items with all properties preserved.
    Should include type, dataset_guid, optional fields, and add URL to each item.
    """
    mock_get, mock_response = mock_data_library_response
    mock_file_instance, mock_file_class = mock_gen3file

    # Mock data library response with GA4GH_DRS items
    list_items = {
        "dg.4503/item1": {
            "type": "GA4GH_DRS",
            "dataset_guid": "phs000007.v35.p16.c1",
            "name": "Item 1",
            "display_name": "Test Item 1",
            "description": "A test item",
        },
        "dg.4503/item2": {
            "type": "GA4GH_DRS",
            "dataset_guid": "phs000008.v36.p17.c2",
            "display_name": "Test Item 2",
        },
    }

    mock_response.json.return_value = {
        "id": "test-list-id",
        "items": list_items,
        "name": "Test List",
        "version": 0,
        "creator": "1",
        "created_time": "2026-07-20T23:54:40.124502+00:00",
        "updated_time": "2026-07-20T23:00:03.532006+00:00",
    }

    mock_file_instance.get_presigned_url.side_effect = [
        {"url": "http://presigned-url-1"},
        {"url": "http://presigned-url-2"},
    ]

    exporter = ListExporter(mock_config)
    result = await exporter.export()

    assert result == [EXPECTED_DRS_ITEM_1, EXPECTED_DRS_ITEM_2]


@pytest.mark.asyncio
async def test_list_exporter_graphql_items(
    mock_config, mock_data_library_response, mock_gen3auth, mock_gen3jobs
):
    """
    Verify that ListExporter exports Gen3GraphQL items with schema preserved.
    Should include name, type, schema_version, query, variables, and add URL to each item.
    """
    mock_get, mock_response = mock_data_library_response
    mock_jobs_instance, mock_jobs_class = mock_gen3jobs

    # Mock data library response with Gen3GraphQL items
    list_items = {
        "graphql-item-1": {
            "type": "Gen3GraphQL",
            "name": "GraphQL Export 1",
            "schema_version": "1.0",
            "data": {
                "query": "{ project { code } }",
                "variables": {"filter": {"project": {"code": "TEST"}}},
            },
        },
        "graphql-item-2": {
            "type": "Gen3GraphQL",
            "name": "GraphQL Export 2",
            "schema_version": "1.0",
            "data": {
                "query": "{ subject { submitter_id } }",
                "variables": {"filter": {}},
            },
        },
    }

    mock_response.json.return_value = {
        "id": "test-list-id",
        "items": list_items,
        "name": "Test List",
        "version": 0,
        "creator": "1",
        "created_time": "2026-07-20T23:54:40.124502+00:00",
        "updated_time": "2026-07-20T23:00:03.532006+00:00",
    }

    mock_jobs_instance.async_run_job_and_wait.side_effect = [
        {"output": "http://job-output-1"},
        {"output": "http://job-output-2"},
    ]

    exporter = ListExporter(mock_config)
    result = await exporter.export()

    assert result == [EXPECTED_GRAPHQL_ITEM_1, EXPECTED_GRAPHQL_ITEM_2]


@pytest.mark.asyncio
async def test_list_exporter_mixed_item_types(
    mock_config, mock_data_library_response, mock_gen3auth, mock_gen3file, mock_gen3jobs
):
    """
    Verify that ListExporter correctly handles mixed GA4GH_DRS and Gen3GraphQL items.
    Each item type should be processed with appropriate exporter and preserve all properties.
    """
    mock_get, mock_response = mock_data_library_response
    mock_file_instance, mock_file_class = mock_gen3file
    mock_jobs_instance, mock_jobs_class = mock_gen3jobs

    # Mock data library response with mixed items
    list_items = {
        "dg.4503/item1": {
            "type": "GA4GH_DRS",
            "dataset_guid": "phs000007.v35.p16.c1",
            "name": "Item 1",
            "display_name": "Test Item 1",
            "description": "A test item",
        },
        "graphql-item-1": {
            "type": "Gen3GraphQL",
            "name": "GraphQL Export 1",
            "schema_version": "1.0",
            "data": {
                "query": "{ project { code } }",
                "variables": {"filter": {"project": {"code": "TEST"}}},
            },
        },
    }

    mock_response.json.return_value = {
        "id": "test-list-id",
        "items": list_items,
        "name": "Test List",
        "version": 0,
        "creator": "1",
        "created_time": "2026-07-20T23:54:40.124502+00:00",
        "updated_time": "2026-07-20T23:00:03.532006+00:00",
    }

    mock_file_instance.get_presigned_url.return_value = {
        "url": "http://presigned-url-1"
    }
    mock_jobs_instance.async_run_job_and_wait.return_value = {
        "output": "http://job-output-1"
    }

    exporter = ListExporter(mock_config)
    result = await exporter.export()

    assert result == [EXPECTED_DRS_ITEM_1, EXPECTED_GRAPHQL_ITEM_1]


@pytest.mark.asyncio
async def test_list_exporter_filtered_items(
    mock_config, mock_data_library_response, mock_gen3auth, mock_gen3file, mock_gen3jobs
):
    """
    Verify that ListExporter filters items based on the items list in config.
    Only specified items should be exported, others should be skipped.
    """
    mock_get, mock_response = mock_data_library_response
    mock_file_instance, mock_file_class = mock_gen3file
    mock_jobs_instance, mock_jobs_class = mock_gen3jobs

    mock_config.get_export_info.return_value = {
        "list_id": "test-list-id",
        "items": ["dg.4503/item1", "graphql-item-1"],  # Only export these two
    }

    # Mock data library has 4 items total
    list_items = {
        "dg.4503/item1": {
            "type": "GA4GH_DRS",
            "dataset_guid": "phs000007.v35.p16.c1",
            "name": "Item 1",
            "display_name": "Test Item 1",
            "description": "A test item",
        },
        "dg.4503/item2": {
            "type": "GA4GH_DRS",
            "dataset_guid": "phs000008.v36.p17.c2",
            "display_name": "Test Item 2",
        },
        "graphql-item-1": {
            "type": "Gen3GraphQL",
            "name": "GraphQL Export 1",
            "schema_version": "1.0",
            "data": {
                "query": "{ project { code } }",
                "variables": {"filter": {"project": {"code": "TEST"}}},
            },
        },
        "graphql-item-2": {
            "type": "Gen3GraphQL",
            "name": "GraphQL Export 2",
            "schema_version": "1.0",
            "data": {
                "query": "{ subject { submitter_id } }",
                "variables": {"filter": {}},
            },
        },
    }

    mock_response.json.return_value = {
        "id": "test-list-id",
        "items": list_items,
        "name": "Test List",
        "version": 0,
        "creator": "1",
        "created_time": "2026-07-20T23:54:40.124502+00:00",
        "updated_time": "2026-07-20T23:00:03.532006+00:00",
    }

    mock_file_instance.get_presigned_url.return_value = {
        "url": "http://presigned-url-1"
    }
    mock_jobs_instance.async_run_job_and_wait.return_value = {
        "output": "http://job-output-1"
    }

    exporter = ListExporter(mock_config)
    result = await exporter.export()

    assert result == [EXPECTED_DRS_ITEM_1, EXPECTED_GRAPHQL_ITEM_1]
    assert len(result) == 2
