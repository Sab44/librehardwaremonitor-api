import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock

import aiohttp
from aiohttp import BasicAuth
from aiohttp import ClientSession

from librehardwaremonitor_api import LibreHardwareMonitorConnectionError
from librehardwaremonitor_api import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api import LibreHardwareMonitorUnauthorizedError
from librehardwaremonitor_api.client import DEFAULT_TIMEOUT
from librehardwaremonitor_api.client import LibreHardwareMonitorClient

from librehardwaremonitor_api.model import LibreHardwareMonitorData
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser


class TestClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.test_json_data = {"dummy": "data"}
        self.mock_session = self._build_session_mock(json_return=self.test_json_data)
        self.client = self._build_client(session=self.mock_session, username=None, password=None)

        self.mock_data = Mock(LibreHardwareMonitorData)
        self.mock_parser = Mock(LibreHardwareMonitorParser)
        self.mock_parser.parse_data.return_value = self.mock_data
        self.client._parser = self.mock_parser

    def _build_client(
        self,
        session: ClientSession,
        host: str = "192.168.1.100",
        port: int = 8085,
        username: str | None = "sab",
        password: str | None = "s3cr3t",
    ) -> LibreHardwareMonitorClient:
        return LibreHardwareMonitorClient(
            host=host, port=port, username=username, password=password, session=session
        )

    def _build_session_mock(
        self, *, json_return: dict[str, str] | None = None, raise_for_status: Exception | None = None
    ) -> AsyncMock:
        response_mock = AsyncMock()
        response_mock.json = AsyncMock(return_value=json_return)
        response_mock.raise_for_status = Mock(side_effect=raise_for_status)

        session_mock = AsyncMock()
        session_mock.get = AsyncMock(return_value=response_mock)
        session_mock.__aenter__.return_value = session_mock

        return session_mock

    async def test_get_data_success_without_auth(self) -> None:
        result = await self.client.get_data()
        assert result == self.mock_data

        self.mock_parser.parse_data.assert_called_once_with(self.test_json_data)
        self._assert_request_params(auth_expected=False)

    async def test_get_data_success_with_auth(self) -> None:
        auth_client = self._build_client(session=self.mock_session)
        auth_client._parser = self.mock_parser

        result = await auth_client.get_data()
        assert result == self.mock_data

        self.mock_parser.parse_data.assert_called_once_with(self.test_json_data)
        self._assert_request_params(auth_expected=True)

    async def test_no_auth_set_if_username_is_missing(self) -> None:
        client = self._build_client(session=self.mock_session, username=None)
        client._parser = self.mock_parser

        result = await self.client.get_data()
        assert result == self.mock_data

        self._assert_request_params(auth_expected=False)

    async def test_no_auth_set_if_password_is_missing(self) -> None:
        client = self._build_client(session=self.mock_session, password=None)
        client._parser = self.mock_parser

        result = await self.client.get_data()
        assert result == self.mock_data

        self._assert_request_params(auth_expected=False)

    async def test_get_data_unauthorized_raises_error(self) -> None:
        error = aiohttp.ClientResponseError(request_info=MagicMock(), history=(), status=401)
        mock_session_with_error = self._build_session_mock(raise_for_status=error)
        client = self._build_client(session=mock_session_with_error)

        with self.assertRaises(LibreHardwareMonitorUnauthorizedError):
            await client.get_data()

    async def test_get_data_other_response_error_raises_connection_error(self) -> None:
        error = aiohttp.ClientResponseError(request_info=MagicMock(), history=(), status=500)
        mock_session_with_error = self._build_session_mock(raise_for_status=error)
        client = self._build_client(session=mock_session_with_error)

        with self.assertRaises(LibreHardwareMonitorConnectionError) as ctx:
            await client.get_data()

        assert ctx.exception.__cause__ == error

    async def test_get_data_no_devices_error_is_propagated(self) -> None:
        self.mock_parser.parse_data.side_effect = LibreHardwareMonitorNoDevicesError

        with self.assertRaises(LibreHardwareMonitorNoDevicesError):
            await self.client.get_data()

    async def test_get_data_unexpected_error_raises_connection_error(self) -> None:
        unexpected_error = RuntimeError("something went wrong")
        self.mock_parser.parse_data.side_effect = unexpected_error

        with self.assertRaises(LibreHardwareMonitorConnectionError) as ctx:
            await self.client.get_data()

        assert ctx.exception.__cause__ == unexpected_error

    def _assert_request_params(self, auth_expected: bool) -> None:
        self.mock_session.get.assert_awaited_once()
        args, kwargs = self.mock_session.get.await_args
        assert args[0] == "http://192.168.1.100:8085/data.json"
        assert kwargs["timeout"] == aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        auth = kwargs["auth"]
        if auth_expected:
            assert auth == BasicAuth(login="sab", password="s3cr3t")
        else:
            assert auth is None
