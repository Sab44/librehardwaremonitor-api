from dataclasses import dataclass
from types import MappingProxyType
from typing import NewType
from typing import Self

from librehardwaremonitor_api.sensor_type import SensorType

DeviceId = NewType("DeviceId", str)
DeviceName = NewType("DeviceName", str)


@dataclass(frozen=True)
class LibreHardwareMonitorSensorData:
    """Data class to hold all data for a specific sensor."""

    name: str
    value: str | None
    type: SensorType | None
    min: str | None
    max: str | None
    unit: str | None
    device_id: str
    device_name: str
    device_type: str
    sensor_id: str


@dataclass(frozen=True, order=True)
class LibreHardwareMonitorVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, version_str: str) -> Self:
        """Parses a string 'X.Y.Z' into a LibreHardwareMonitorVersion object."""
        parts = [int(p) for p in version_str.split(".")]

        if len(parts) != 3:
            raise ValueError("Version must have exactly three parts (major.minor.patch)")

        return cls(*parts)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class LibreHardwareMonitorData:
    """Data class to hold device names and data for all sensors."""

    computer_name: str
    main_device_ids_and_names: MappingProxyType[DeviceId, DeviceName]
    sensor_data: MappingProxyType[str, LibreHardwareMonitorSensorData]
    version: LibreHardwareMonitorVersion
    is_deprecated_version: bool
