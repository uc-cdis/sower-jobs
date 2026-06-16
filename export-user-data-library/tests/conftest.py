import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def mock_config():
    """Mock ConfigProvider - used by multiple ListExporter tests"""
    config = Mock()
    config.get_access_token.return_value = "test-token"
    config.get_data_library_service.return_value = "http://test-library"
    config.get_export_info.return_value = {"list_id": "test-list-id", "items": []}
    return config


@pytest.fixture
def mock_data_library_response():
    """Mock data library HTTP response - used by multiple ListExporter tests"""
    with patch("export_user_data_library.export.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {"content-type": "application/json"}
        mock_get.return_value = mock_response
        yield mock_get, mock_response


@pytest.fixture
def mock_gen3auth():
    """Mock Gen3Auth initialization - used by multiple ListExporter tests"""
    with patch("export_user_data_library.export.Gen3Auth"):
        yield


@pytest.fixture
def mock_gen3file():
    """Mock Gen3File for DRS exporter - used by multiple ListExporter tests"""
    with patch("export_user_data_library.export.Gen3File") as mock_file_class:
        mock_file_instance = Mock()
        mock_file_class.return_value = mock_file_instance
        yield mock_file_instance, mock_file_class


@pytest.fixture
def mock_gen3jobs():
    """Mock Gen3Jobs for GraphQL exporter - used by multiple ListExporter tests"""
    with patch("export_user_data_library.export.Gen3Jobs") as mock_jobs_class:
        mock_jobs_instance = AsyncMock()
        mock_jobs_class.return_value = mock_jobs_instance
        yield mock_jobs_instance, mock_jobs_class
