"""Client for the LibreHardwareMonitor API."""

import aiohttp

from librehardwaremonitor_api.errors import LibreHardwareMonitorConnectionError
from librehardwaremonitor_api.errors import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.model import LibreHardwareMonitorData
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser

DEFAULT_TIMEOUT = 5


class LibreHardwareMonitorClient:
    """Class to communicate with the LibreHardwareMonitor Endpoint."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the API."""
        self._data_url = f"http://{host}:{port}/data.json"
        self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        self._parser = LibreHardwareMonitorParser()


    async def get_data(self) -> LibreHardwareMonitorData:
        """Get the latest data from the LibreHardwareMonitor API."""
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                response = await session.get(self._data_url)
                lhm_data = await response.json()
                return self._parser.parse_data(lhm_data)
        except LibreHardwareMonitorNoDevicesError:
            raise
        except Exception as exception:  # pylint: disable=broad-except
            raise LibreHardwareMonitorConnectionError(exception) from exception

