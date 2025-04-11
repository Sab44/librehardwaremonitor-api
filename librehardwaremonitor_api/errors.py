class LibreHardwareMonitorConnectionError(Exception):
    """Could not connect to LibreHardwareMonitor instance."""


class LibreHardwareMonitorNoDevicesError(Exception):
    """Received json does not contain any devices with sensor data."""