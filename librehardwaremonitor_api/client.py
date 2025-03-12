"""Client for the LibreHardwareMonitor API."""

import aiohttp

DEFAULT_TIMEOUT = 5

LHM_CHILDREN = "Children"
LHM_ID = "id"
LHM_NAME = "Text"


class LibreHardwareMonitorConnectionError(Exception):
    """Could not connect to LibreHardwareMonitor instance."""


class LibreHardwareMonitorNoDevicesError(Exception):
    """Received json does not contain any devices."""


class LibreHardwareMonitorClient:
    """Class to communicate with the LibreHardwareMonitor Endpoint."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the API."""
        self._data_url = f"http://{host}:{port}/data.json"
        self._timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)

    async def get_data_json(self) -> dict:
        """Get the latest data from the LibreHardwareMonitor API."""

        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                response = await session.get(self._data_url)
                return await response.json()
        except Exception as exception:  # pylint: disable=broad-except
            raise LibreHardwareMonitorConnectionError(exception) from exception

    async def get_hardware_device_names(self) -> list[str]:
        """Get the main device ids and names from the computer."""
        lhm_json = await self.get_data_json()

        monitored_computer = lhm_json[LHM_CHILDREN]
        main_devices: list[str] = []

        if monitored_computer[0]:
            main_devices.extend(
                device[LHM_NAME] for device in monitored_computer[0][LHM_CHILDREN]
            )

        if not main_devices:
            raise LibreHardwareMonitorNoDevicesError from None

        return main_devices