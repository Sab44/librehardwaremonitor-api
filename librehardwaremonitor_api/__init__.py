"""LibreHardwareMonitor API library"""

from librehardwaremonitor_api.client import LibreHardwareMonitorClient
from librehardwaremonitor_api.errors import LibreHardwareMonitorConnectionError
from librehardwaremonitor_api.errors import LibreHardwareMonitorNoDevicesError

__all__ = [
    "LibreHardwareMonitorClient",
    "LibreHardwareMonitorConnectionError",
    "LibreHardwareMonitorNoDevicesError",
]
