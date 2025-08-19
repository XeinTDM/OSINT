import pytest
import os
import json
from unittest.mock import AsyncMock, Mock, patch, mock_open
import aiohttp
from modules.sites_manager import SitesManager
from modules import paths
from modules.core.site_models import CountrySites

# Mock the SITES_JSON_PATH and FULL_NAME_SITES_JSON_PATH for testing
@pytest.fixture(autouse=True)
def mock_sites_json_paths(tmp_path):
    original_sites_path = paths.SITES_JSON_PATH
    original_full_name_sites_path = paths.FULL_NAME_SITES_JSON_PATH

    mock_sites_path = tmp_path / "data" / "sites.json"
    mock_full_name_sites_path = tmp_path / "data" / "full_name_sites.json"

    os.makedirs(os.path.dirname(mock_sites_path), exist_ok=True)
    os.makedirs(os.path.dirname(mock_full_name_sites_path), exist_ok=True)

    paths.SITES_JSON_PATH = str(mock_sites_path)
    paths.FULL_NAME_SITES_JSON_PATH = str(mock_full_name_sites_path)

    yield

    paths.SITES_JSON_PATH = original_sites_path
    paths.FULL_NAME_SITES_JSON_PATH = original_full_name_sites_path

@pytest.mark.asyncio
async def test_ensure_sites_json_exists_creates_files_if_not_found(mock_sites_json_paths):
    

    # Create separate mock_open instances for each expected file operation
    mock_file_sites_write = mock_open()
    mock_file_full_name_write = mock_open()

    with (
        patch("os.path.exists", side_effect=[False, False]), # sites.json not found, then full_name_sites.json not found
        patch("builtins.open") as mocked_open, # Patch builtins.open directly
        patch("os.makedirs"),
        patch("aiohttp.ClientSession", side_effect=aiohttp.ClientError("Simulated network error")), # Simulate network error for URL updates
        patch.object(SitesManager, "update_sites_json_from_url", new_callable=AsyncMock) as mock_update_username_sites,
        patch.object(SitesManager, "update_full_name_sites_json_from_url", new_callable=AsyncMock),
        patch.object(SitesManager, "_load_sites_data") # Prevent _load_sites_data from running during init
    ):
        mocked_open.side_effect = [
            mock_file_sites_write.return_value,
            mock_file_full_name_write.return_value
        ]
        manager = SitesManager()
        # No longer setting return_value to False, let the actual methods run and fail due to aiohttp mock

        await manager.ensure_sites_json_exists()

        mock_update_username_sites.assert_called_once()
        

        assert manager._username_sites_data == []
        assert manager._full_name_sites_data == []

@pytest.mark.asyncio
async def test_ensure_sites_json_exists_loads_existing_files(mock_sites_json_paths):
    mock_username_content = {"username_sites": [{"name": "test_user", "url": "http://test.com"}]}
    mock_full_name_content = [{"country": "Test", "sites": []}]

    m_open = mock_open()
    m_open.side_effect = [
        mock_open(read_data=json.dumps(mock_username_content)).return_value, # sites.json read
        mock_open(read_data=json.dumps(mock_full_name_content)).return_value # full_name_sites.json read
    ]

    with (
        patch("os.path.exists", side_effect=[True, True]), # sites.json found, then full_name_sites.json found
        patch("builtins.open", m_open) as mocked_open,
    ):
        manager = SitesManager()
        await manager.ensure_sites_json_exists()

        mocked_open.assert_any_call(paths.SITES_JSON_PATH, "r", encoding="utf-8")
        mocked_open.assert_any_call(paths.FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8")
        assert manager._username_sites_data == mock_username_content["username_sites"]
        assert manager._full_name_sites_data == [CountrySites(country=d["country"], sites=d["sites"]) for d in mock_full_name_content]

@pytest.mark.asyncio
async def test_ensure_sites_json_exists_handles_json_decode_error(mock_sites_json_paths):
    m_open = mock_open()
    m_open.side_effect = [
        mock_open(read_data="invalid json").return_value, # sites.json read
        mock_open(read_data="invalid json").return_value # full_name_sites.json read
    ]

    with (
        patch("os.path.exists", side_effect=[True, True]),
        patch("builtins.open", m_open) as mocked_open,
    ):
        manager = SitesManager()
        await manager.ensure_sites_json_exists()

        mocked_open.assert_any_call(paths.SITES_JSON_PATH, "r", encoding="utf-8")
        mocked_open.assert_any_call(paths.FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8")
        assert manager._username_sites_data == []
        assert manager._full_name_sites_data == []

@pytest.mark.asyncio
async def test_update_sites_json_from_url_success(mock_sites_json_paths):
    mock_response_text = json.dumps({"username_sites": [{"name": "new_site", "url": "http://new.com"}]}, indent=2)

    mock_response_obj = Mock()
    mock_response_obj.text = AsyncMock(return_value=mock_response_text)
    mock_response_obj.raise_for_status.return_value = None

    mock_client_response_context = AsyncMock()
    mock_client_response_context.__aenter__.return_value = mock_response_obj
    mock_client_response_context.__aexit__.return_value = None

    mock_session_context = AsyncMock(spec=aiohttp.ClientSession)
    mock_session_context.__aenter__.return_value = mock_session_context
    mock_session_context.__aexit__.return_value = None
    mock_session_context.get.return_value = mock_client_response_context

    with (
        patch("aiohttp.ClientSession", return_value=mock_session_context),
        patch("builtins.open", mock_open()) as mocked_open,
        patch("os.makedirs"),
        patch.object(SitesManager, "_load_sites_data") # Prevent _load_sites_data from running during init
    ):
        manager = SitesManager()
        result = await manager.update_sites_json_from_url()

        mock_session_context.get.assert_called_once_with("https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/sites.json", timeout=10)
        mocked_open.assert_called_with(paths.SITES_JSON_PATH, "w", encoding="utf-8")
        handle = mocked_open()
        written_content = "".join(call_args.args[0] for call_args in handle.write.call_args_list)
        assert written_content == mock_response_text
        assert result is True
        assert manager._username_sites_data == json.loads(mock_response_text)["username_sites"]

@pytest.mark.asyncio
async def test_update_full_name_sites_json_from_url_success(mock_sites_json_paths):
    mock_response_text = json.dumps([{"country": "New", "sites": []}], indent=2)

    mock_response_obj = Mock()
    mock_response_obj.text = AsyncMock(return_value=mock_response_text)
    mock_response_obj.raise_for_status.return_value = None

    mock_client_response_context = AsyncMock()
    mock_client_response_context.__aenter__.return_value = mock_response_obj
    mock_client_response_context.__aexit__.return_value = None

    mock_session_context = AsyncMock(spec=aiohttp.ClientSession)
    mock_session_context.__aenter__.return_value = mock_session_context
    mock_session_context.__aexit__.return_value = None
    mock_session_context.get.return_value = mock_client_response_context

    with (
        patch("aiohttp.ClientSession", return_value=mock_session_context),
        patch("builtins.open", mock_open()) as mocked_open,
        patch("os.makedirs"),
        patch.object(SitesManager, "_load_sites_data") # Prevent _load_sites_data from running during init
    ):
        manager = SitesManager()
        result = await manager.update_full_name_sites_json_from_url("http://example.com/full_name_sites.json")

        mock_session_context.get.assert_called_once_with("http://example.com/full_name_sites.json", timeout=10)
        mocked_open.assert_called_with(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8")
        handle = mocked_open()
        written_content = "".join(call_args.args[0] for call_args in handle.write.call_args_list)
        assert written_content == mock_response_text
        assert result is True
        assert manager._full_name_sites_data == json.loads(mock_response_text)

@pytest.mark.asyncio
async def test_update_sites_json_from_url_client_error(mock_sites_json_paths):
    mock_response_obj = Mock()
    mock_response_obj.raise_for_status.side_effect = aiohttp.ClientError("Connection failed")
    mock_response_obj.text = AsyncMock(return_value="{}")

    mock_client_response_context = AsyncMock()
    mock_client_response_context.__aenter__.return_value = mock_response_obj
    mock_client_response_context.__aexit__.return_value = None

    mock_session_context = AsyncMock(spec=aiohttp.ClientSession)
    mock_session_context.__aenter__.return_value = mock_session_context
    mock_session_context.__aexit__.return_value = None
    mock_session_context.get.return_value = mock_client_response_context

    with (
        patch("aiohttp.ClientSession", return_value=mock_session_context),
        patch("modules.sites_manager.logger.error") as mock_logger_error,
        patch.object(SitesManager, "_load_sites_data") # Prevent _load_sites_data from running during init
    ):
        manager = SitesManager()
        result = await manager.update_sites_json_from_url()

        mock_logger_error.assert_called_once_with("Failed to fetch sites.json from URL: Connection failed")
        assert result is False

@pytest.mark.asyncio
async def test_update_sites_json_from_url_unexpected_error(mock_sites_json_paths):
    mock_response_obj = Mock()
    mock_response_obj.raise_for_status.side_effect = Exception("Unexpected error")
    mock_response_obj.text = AsyncMock(return_value="{}")

    mock_client_response_context = AsyncMock()
    mock_client_response_context.__aenter__.return_value = mock_response_obj
    mock_client_response_context.__aexit__.return_value = None

    mock_session_context = AsyncMock(spec=aiohttp.ClientSession)
    mock_session_context.__aenter__.return_value = mock_session_context
    mock_session_context.__aexit__.return_value = None
    mock_session_context.get.return_value = mock_client_response_context

    with (
        patch("aiohttp.ClientSession", return_value=mock_session_context),
        patch("modules.sites_manager.logger.error") as mock_logger_error,
        patch.object(SitesManager, "_load_sites_data") # Prevent _load_sites_data from running during init
    ):
        manager = SitesManager()
        result = await manager.update_sites_json_from_url()

        mock_logger_error.assert_called_once_with("An unexpected error occurred while updating sites.json: Unexpected error")
        assert result is False