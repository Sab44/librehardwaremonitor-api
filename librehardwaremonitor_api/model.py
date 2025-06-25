from dataclasses import dataclass

@dataclass
class LibreHardwareMonitorSensorData:
    """Data class to hold all data for a specific sensor."""
    name: str
    value: str
    min: str
    max: str
    unit: str | None
    device_id: str
    device_name: str
    device_type: str
    sensor_id: str


@dataclass
class LibreHardwareMonitorData:
    """Data class to hold device names and data for all sensors."""
    main_device_names: list[str]
    sensor_data: dict[str, LibreHardwareMonitorSensorData]