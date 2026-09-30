from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock

import aiohttp
import pytest
from aiohttp import BasicAuth
from aiohttp import ClientSession

from librehardwaremonitor_api import LibreHardwareMonitorConnectionError
from librehardwaremonitor_api import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api import LibreHardwareMonitorUnauthorizedError
from librehardwaremonitor_api.client import DEFAULT_TIMEOUT
from librehardwaremonitor_api.client import LibreHardwareMonitorClient

from librehardwaremonitor_api.model import LibreHardwareMonitorData
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser

TEST_JSON_DATA = {"dummy": "data"}


@pytest.fixture
def mock_session() -> AsyncMock:
    return _build_session_mock(json_return=TEST_JSON_DATA)


@pytest.fixture
def mock_parser() -> Mock:
    mock_parser = Mock(LibreHardwareMonitorParser)
    mock_parser.parse_data.return_value = Mock(LibreHardwareMonitorData)
    return mock_parser


@pytest.fixture
def client(mock_session: AsyncMock, mock_parser: Mock) -> LibreHardwareMonitorClient:
    return _build_client(session=mock_session, parser=mock_parser)


@pytest.mark.parametrize(
    ("username", "password", "expected_auth"),
    [
        pytest.param(None, None, None, id="without_auth"),
        pytest.param("sab", "s3cr3t", BasicAuth(login="sab", password="s3cr3t"), id="with_auth"),
        pytest.param(None, "s3cr3t", None, id="username_missing"),
        pytest.param("sab", None, None, id="password_missing"),
    ],
)
async def test_get_data_success(
    mock_session: AsyncMock,
    mock_parser: Mock,
    username: str | None,
    password: str | None,
    expected_auth: BasicAuth | None,
) -> None:
    client = _build_client(session=mock_session, parser=mock_parser, username=username, password=password)

    result = await client.get_data()

    assert result == mock_parser.parse_data.return_value
    mock_parser.parse_data.assert_called_once_with(TEST_JSON_DATA)
    mock_session.get.assert_awaited_once_with(
        "http://192.168.1.100:8085/data.json",
        auth=expected_auth,
        timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
    )


async def test_get_data_unauthorized_raises_error(mock_parser: Mock) -> None:
    error = aiohttp.ClientResponseError(request_info=MagicMock(), history=(), status=401)
    client = _build_client(session=_build_session_mock(raise_for_status=error), parser=mock_parser)

    with pytest.raises(LibreHardwareMonitorUnauthorizedError):
        await client.get_data()


async def test_get_data_other_response_error_raises_connection_error(mock_parser: Mock) -> None:
    error = aiohttp.ClientResponseError(request_info=MagicMock(), history=(), status=500)
    client = _build_client(session=_build_session_mock(raise_for_status=error), parser=mock_parser)

    with pytest.raises(LibreHardwareMonitorConnectionError) as exc_info:
        await client.get_data()

    assert exc_info.value.__cause__ == error


async def test_get_data_no_devices_error_is_propagated(
    client: LibreHardwareMonitorClient, mock_parser: Mock
) -> None:
    mock_parser.parse_data.side_effect = LibreHardwareMonitorNoDevicesError

    with pytest.raises(LibreHardwareMonitorNoDevicesError):
        await client.get_data()


async def test_get_data_unexpected_error_raises_connection_error(
    client: LibreHardwareMonitorClient, mock_parser: Mock
) -> None:
    unexpected_error = RuntimeError("something went wrong")
    mock_parser.parse_data.side_effect = unexpected_error

    with pytest.raises(LibreHardwareMonitorConnectionError) as exc_info:
        await client.get_data()

    assert exc_info.value.__cause__ == unexpected_error


def _build_client(
    session: ClientSession,
    parser: Mock,
    username: str | None = None,
    password: str | None = None,
) -> LibreHardwareMonitorClient:
    client = LibreHardwareMonitorClient(
        host="192.168.1.100", port=8085, username=username, password=password, session=session
    )
    client._parser = parser
    return client


def _build_session_mock(
    *, json_return: dict[str, str] | None = None, raise_for_status: Exception | None = None
) -> AsyncMock:
    response_mock = AsyncMock()
    response_mock.json = AsyncMock(return_value=json_return)
    response_mock.raise_for_status = Mock(side_effect=raise_for_status)

    session_mock = AsyncMock()
    session_mock.get = AsyncMock(return_value=response_mock)
    session_mock.__aenter__.return_value = session_mock

    return session_mock
