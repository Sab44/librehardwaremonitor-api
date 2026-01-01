class LibreHardwareMonitorConnectionError(Exception):
    """Could not connect to LibreHardwareMonitor instance."""


class LibreHardwareMonitorUnauthorizedError(Exception):
    """Could not authenticate against LibreHardwareMonitor web server."""


class LibreHardwareMonitorNoDevicesError(Exception):
    """Received json does not contain any devices with sensor data."""
