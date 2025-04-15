"""Client for the LibreHardwareMonitor API."""
from typing import Any

import aiohttp

from librehardwaremonitor_api.errors import LibreHardwareMonitorConnectionError
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
        lhm_data = await self._fetch_data_json()
        return self._parser.parse_data(lhm_data)

    async def get_main_hardware_devices(self) -> list[str]:
        """Get the main device ids and names from the computer."""
        lhm_data = await self._fetch_data_json()
        return self._parser.parse_main_hardware_device_names(lhm_data)

    async def _fetch_data_json(self) -> dict[str, Any]:
        """Get the json provided by the Libre Hardware Monitor web server."""
        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                response = await session.get(self._data_url)
                return await response.json()
        except Exception as exception:  # pylint: disable=broad-except
            raise LibreHardwareMonitorConnectionError(exception) from exception
