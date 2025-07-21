from dataclasses import dataclass
from types import MappingProxyType
from typing import NewType

DeviceId = NewType("DeviceId", str)
DeviceName = NewType("DeviceName", str)

@dataclass(frozen=True)
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


@dataclass(frozen=True)
class LibreHardwareMonitorData:
    """Data class to hold device names and data for all sensors."""
    main_device_ids_and_names: MappingProxyType[DeviceId, DeviceName]
    sensor_data: MappingProxyType[str, LibreHardwareMonitorSensorData]