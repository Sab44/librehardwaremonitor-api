from dataclasses import dataclass

@dataclass
class LibreHardwareMonitorSensorData:
    """Data class to hold all relevant sensor data."""
    name: str
    value: str
    min: str
    max: str
    unit: str | None
    device_name: str
    device_type: str
    sensor_id: str

@dataclass
class LibreHardwareMonitorData:
    """Data class to hold device names and sensor data."""
    main_device_names: list[str]
    sensor_data: dict[str, LibreHardwareMonitorSensorData]