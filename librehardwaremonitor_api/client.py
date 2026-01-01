"""Client for the LibreHardwareMonitor API."""

import aiohttp
from aiohttp import BasicAuth
from aiohttp import ClientResponseError
from aiohttp import ClientSession

from librehardwaremonitor_api.errors import LibreHardwareMonitorConnectionError
from librehardwaremonitor_api.errors import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.errors import LibreHardwareMonitorUnauthorizedError
from librehardwaremonitor_api.model import LibreHardwareMonitorData
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser

DEFAULT_TIMEOUT = 5


class LibreHardwareMonitorClient:
    """Class to communicate with the LibreHardwareMonitor Endpoint."""

    def __init__(
        self,
        host: str,
        port: int,
        session: ClientSession | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the API."""
        self._parser = LibreHardwareMonitorParser()
        self._session = session or aiohttp.ClientSession()
        self._data_url = f"http://{host}:{port}/data.json"
        self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        self._auth: BasicAuth | None = None
        if username is not None and password is not None:
            self._auth = BasicAuth(login=username, password=password)

    async def get_data(self) -> LibreHardwareMonitorData:
        """Get the latest data from the LibreHardwareMonitor API."""
        try:
            async with self._session as session:
                response = await session.get(self._data_url, auth=self._auth, timeout=self._timeout)
                response.raise_for_status()
                lhm_data = await response.json()
                return self._parser.parse_data(lhm_data)
        except ClientResponseError as response_error:
            if response_error.status == 401:
                raise LibreHardwareMonitorUnauthorizedError
            raise LibreHardwareMonitorConnectionError(response_error) from response_error
        except LibreHardwareMonitorNoDevicesError:
            raise
        except Exception as exception:  # pylint: disable=broad-except
            raise LibreHardwareMonitorConnectionError(exception) from exception
