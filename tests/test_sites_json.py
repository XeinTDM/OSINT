import pytest
import os
import json
from unittest.mock import AsyncMock, Mock, patch, mock_open, ANY
import aiohttp
from modules.sites_manager import SitesManager
from modules import paths
from modules.core.site_models import CountrySites, Site
from modules.enums import CheckMethods, ErrorTypes, HttpMethod, ResponseType, CheckTypes

MINIMAL_VALID_SITE_DICT = {
    "id": "test_site",
    "name": "Test Site",
    "homeUrl": "http://test.com",
    "urlTemplate": "http://test.com/{username}",
    "placeholders": ["username"],
    "urlEncode": False,
    "method": HttpMethod.GET.value,
    "responseType": ResponseType.HTML.value,
    "requiresJs": False,
    "noResult": {"type": "status_code", "value": "404"},
    "checkMethod": CheckMethods.BASIC.value,
    "errorType": ErrorTypes.STATUS_CODE.value,
    "checkType": CheckTypes.NEGATIVE.value,
    "errorString": None,
    "successString": None,
    "headers": {},
    "resultMatcher": None,
    "extract": None,
    "pagination": None,
    "rateLimitPerMinute": None,
    "timeoutSeconds": None,
    "retries": None,
    "lastVerified": None,
    "active": True,
    "legal": None,
    "tags": [],
    "notes": None,
    "advanced_placeholders": [],
}

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
    with (
        patch("os.path.exists", side_effect=[False, False, True, True]),
        patch("os.makedirs"),
        patch("aiohttp.ClientSession", side_effect=aiohttp.ClientError("Simulated network error")),
        patch.object(SitesManager, "_create_default_username_sites_json"),
        patch.object(SitesManager, "_create_default_full_name_sites_json"),
        patch.object(SitesManager, "update_sites_json_from_url", new_callable=AsyncMock) as mock_update_username_sites,
        patch.object(SitesManager, "update_full_name_sites_json_from_url", new_callable=AsyncMock) as mock_update_full_name_sites,
        patch.object(SitesManager, "_load_username_sites_data_from_file", return_value=[]),
        patch.object(SitesManager, "_load_full_name_sites_data_from_file", return_value=[]),
    ):
        manager = SitesManager()

        await manager.ensure_sites_json_exists()
        mock_update_username_sites.assert_called_once()
        mock_update_full_name_sites.assert_called_once()

        assert manager._username_sites_data == []
        assert manager._full_name_sites_data == []

@pytest.mark.asyncio
async def test_ensure_sites_json_exists_loads_existing_files(mock_sites_json_paths):
    mock_username_content = {"username_sites": [Site.model_validate(MINIMAL_VALID_SITE_DICT).model_dump(mode='json')]}
    mock_full_name_content = [CountrySites.model_validate({"country": "Test", "sites": [MINIMAL_VALID_SITE_DICT]}).model_dump(mode='json')]

    with (
        patch("os.path.exists", side_effect=[True, True]),
        patch.object(SitesManager, "_load_username_sites_data_from_file", return_value=[Site.model_validate(MINIMAL_VALID_SITE_DICT)]),
        patch.object(SitesManager, "_load_full_name_sites_data_from_file", return_value=[CountrySites.model_validate({"country": "Test", "sites": [MINIMAL_VALID_SITE_DICT]} )]),
    ):
        manager = SitesManager()
        await manager.ensure_sites_json_exists()

        assert all(isinstance(s, Site) for s in manager._username_sites_data)
        assert [s.model_dump(mode='json') for s in manager._username_sites_data] == mock_username_content["username_sites"]
        assert all(isinstance(cs, CountrySites) for cs in manager._full_name_sites_data)
        assert [cs.model_dump(mode='json') for cs in manager._full_name_sites_data] == mock_full_name_content

@pytest.mark.asyncio
async def test_ensure_sites_json_exists_handles_json_decode_error(mock_sites_json_paths):
    m_open = mock_open()
    m_open.side_effect = [
        mock_open(read_data="invalid json").return_value,
        mock_open(read_data="invalid json").return_value
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
async def test_parse_full_name_sites_data_with_validation_error(mock_sites_json_paths):
    manager = SitesManager()
    invalid_data = [
        {"country": "Invalid", "sites": [{"id": "missing_name"}]}
    ]

    with patch("modules.sites_manager.logger.error") as mock_logger_error:
        parsed_data = manager._parse_full_name_sites_data(invalid_data)
        assert parsed_data == []
        mock_logger_error.assert_called_once()
        assert "Validation error parsing country data" in mock_logger_error.call_args[0][0]

@pytest.mark.asyncio
async def test_create_default_full_name_sites_json_reads_from_default_file(mock_sites_json_paths):
    manager = SitesManager()
    mock_default_content = [{"country": "Default", "sites": [MINIMAL_VALID_SITE_DICT]}]

    with (
        patch("builtins.open", new_callable=mock_open) as mocked_open,
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("json.dump") as mock_json_dump,
    ):
        mocked_open.side_effect = [
            mock_open(read_data=json.dumps(mock_default_content)).return_value,
            mock_open().return_value
        ]
        manager._create_default_full_name_sites_json()

        mocked_open.assert_any_call(paths.DEFAULT_FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8")

        mocked_open.assert_any_call(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8")
        mock_json_dump.assert_called_once_with(mock_default_content, ANY, indent=2)

@pytest.mark.asyncio
async def test_update_sites_json_from_url_success(mock_sites_json_paths):
    mock_response_text = json.dumps({"username_sites": [MINIMAL_VALID_SITE_DICT]}, indent=2)

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
    ):
        manager = SitesManager()
        result = await manager.update_sites_json_from_url()

        mock_session_context.get.assert_called_once_with("https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/sites.json", timeout=10)
        mocked_open.assert_called_with(paths.SITES_JSON_PATH, "w", encoding="utf-8")
        handle = mocked_open()
        written_content = "".join(call_args.args[0] for call_args in handle.write.call_args_list)
        assert written_content == mock_response_text
        assert result is True
        assert all(isinstance(s, Site) for s in manager._username_sites_data)
        assert [s.model_dump(mode='json') for s in manager._username_sites_data] == json.loads(mock_response_text)["username_sites"]

@pytest.mark.asyncio
async def test_update_full_name_sites_json_from_url_success(mock_sites_json_paths):
    mock_full_name_site_data = CountrySites.model_validate({"country": "New", "sites": [MINIMAL_VALID_SITE_DICT]})
    mock_response_text = json.dumps([mock_full_name_site_data.model_dump(mode='json')], indent=2)

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
    ):
        manager = SitesManager()
        result = await manager.update_full_name_sites_json_from_url("https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/full_name_sites.json")

        mock_session_context.get.assert_called_once_with("https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/full_name_sites.json", timeout=10)
        mocked_open.assert_called_with(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8")
        handle = mocked_open()
        written_content = "".join(call_args.args[0] for call_args in handle.write.call_args_list)
        assert written_content == mock_response_text
        assert result is True
        assert all(isinstance(cs, CountrySites) for cs in manager._full_name_sites_data)
        assert [cs.model_dump(mode='json') for cs in manager._full_name_sites_data] == json.loads(mock_response_text)

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
    ):
        manager = SitesManager()
        result = await manager.update_sites_json_from_url()

        mock_logger_error.assert_called_once_with("An unexpected error occurred while updating sites.json: Unexpected error")
        assert result is False