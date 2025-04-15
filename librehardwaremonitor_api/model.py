from dataclasses import dataclass

@dataclass
class LibreHardwareMonitorSensorData:
    """Data class to hold all data for a specific sensor."""
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
    """Data class that contains data for all sensors."""
    sensor_data: dict[str, LibreHardwareMonitorSensorData]