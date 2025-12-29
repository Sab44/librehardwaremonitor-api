import re
from types import MappingProxyType
from typing import Any
from typing import Optional

from librehardwaremonitor_api.errors import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.model import DeviceId
from librehardwaremonitor_api.model import DeviceName
from librehardwaremonitor_api.model import LibreHardwareMonitorData
from librehardwaremonitor_api.model import LibreHardwareMonitorSensorData

LHM_CHILDREN = "Children"
LHM_DEVICE_TYPE = "ImageURL"
LHM_HARDWARE_ID = "HardwareId"
LHM_MAX = "Max"
LHM_MIN = "Min"
LHM_NAME = "Text"
LHM_RAW_MAX = "RawMax"
LHM_RAW_MIN = "RawMin"
LHM_RAW_VALUE = "RawValue"
LHM_SENSOR_ID = "SensorId"
LHM_TYPE = "Type"
LHM_VALUE = "Value"


class LibreHardwareMonitorParser:
    def parse_data(self, lhm_data: dict[str, Any]) -> LibreHardwareMonitorData:
        """Get data from all sensors across all devices."""
        computer_name = lhm_data[LHM_CHILDREN][0][LHM_NAME]
        main_device_ids_and_names: dict[DeviceId, DeviceName] = {}
        sensors_data: dict[str, LibreHardwareMonitorSensorData] = {}

        main_devices: list[dict[str, Any]] = lhm_data[LHM_CHILDREN][0][LHM_CHILDREN]
        for main_device in main_devices:
            sensor_data_for_device = self._parse_sensor_data(main_device)

            for sensor_data in sensor_data_for_device:
                sensors_data[sensor_data.sensor_id] = sensor_data

                main_device_id = DeviceId(sensor_data.device_id)
                main_device_name = DeviceName(main_device[LHM_NAME])
                main_device_ids_and_names[main_device_id] = main_device_name

        if not sensors_data:
            raise LibreHardwareMonitorNoDevicesError from None

        return LibreHardwareMonitorData(
            computer_name=computer_name,
            main_device_ids_and_names=MappingProxyType(main_device_ids_and_names),
            sensor_data=MappingProxyType(sensors_data),
        )

    def _parse_sensor_data(self, main_device: dict[str, Any]) -> list[LibreHardwareMonitorSensorData]:
        """Parse all sensors from a given device."""
        device_type = self._parse_device_type(main_device)
        # This will only work for LHM versions > 0.9.4, otherwise we parse device id from sensor id below
        device_id = self._format_id(main_device.get(LHM_HARDWARE_ID))

        sensor_data_for_device: list[LibreHardwareMonitorSensorData] = []
        all_sensors_for_device = self._flatten_sensors(main_device)
        for sensor in all_sensors_for_device:
            sensor_id = re.sub(r"[^a-zA-Z0-9_-]", "", "-".join(sensor[LHM_SENSOR_ID].split("/")[1:]))
            # For versions <= 0.9.4 use legacy method of parsing device id from sensor id
            if not device_id:
                device_id = sensor_id.rsplit("-", 2)[0]

            name: str = sensor[LHM_NAME]
            type: str = sensor[LHM_TYPE]

            value: str | None = sensor[LHM_VALUE].split(" ")[0]
            min: str | None = sensor[LHM_MIN].split(" ")[0]
            max: str | None = sensor[LHM_MAX].split(" ")[0]

            # Replace comma decimal separators e.g. in german locale
            value = value.replace(",", ".") if value is not None else None
            min = min.replace(",", ".") if min is not None else None
            max = max.replace(",", ".") if max is not None else None

            unit = None
            if " " in sensor[LHM_VALUE]:
                unit = sensor[LHM_VALUE].split(" ")[1]

            if type == "Throughput":
                if raw_value := sensor.get(LHM_RAW_VALUE):
                    unit = "KB/s"

                    raw_value = raw_value.split(" ")[0].replace(",", ".")
                    raw_min = sensor[LHM_RAW_MIN].split(" ")[0].replace(",", ".")
                    raw_max = sensor[LHM_RAW_MAX].split(" ")[0].replace(",", ".")

                    try:
                        normalized_value = f"{(float(raw_value) / 1024):.1f}"
                        normalized_min = f"{(float(raw_min) / 1024):.1f}"
                        normalized_max = f"{(float(raw_max) / 1024):.1f}"

                        value = normalized_value
                        min = normalized_min
                        max = normalized_max
                    except ValueError:
                        value = None
                        min = None
                        max = None

            elif type == "TimeSpan":
                unit = "s"

                if raw_value := sensor.get(LHM_RAW_VALUE):
                    value = raw_value
                    min = sensor[LHM_RAW_MIN]
                    max = sensor[LHM_RAW_MAX]
                else:
                    value = self._convert_to_seconds(value)
                    min = self._convert_to_seconds(min)
                    max = self._convert_to_seconds(max)

            value = self._ensure_value_is_numerical(value)
            min = self._ensure_value_is_numerical(min)
            max = self._ensure_value_is_numerical(max)

            sensor_data = LibreHardwareMonitorSensorData(
                name=f"{name} {type}",
                value=value,
                min=min,
                max=max,
                unit=unit,
                device_id=device_id,
                device_name=main_device[LHM_NAME],
                device_type=device_type,
                sensor_id=sensor_id,
            )
            sensor_data_for_device.append(sensor_data)

        return sensor_data_for_device

    def _ensure_value_is_numerical(self, value: str | None) -> str | None:
        """Ensure a given string holds a numerical value."""
        if value is None or value == "NaN":
            return None

        try:
            _ = float(value)
        except ValueError:
            return None

        return value

    def _format_id(self, id: Optional[str]) -> Optional[str]:
        """Format a given ID to remove slashes and undesired characters."""
        if not id:
            return None
        return re.sub(r"[^a-zA-Z0-9_-]", "", "-".join(id.split("/")[1:]))

    def _parse_device_type(self, main_device: dict[str, Any]) -> str:
        """Parse the device type from the image url property."""
        device_type = ""
        if "/" in main_device[LHM_DEVICE_TYPE]:
            device_type = main_device[LHM_DEVICE_TYPE].split("/")[1].split(".")[0]
        return device_type.upper() if device_type != "transparent" else "UNKNOWN"

    def _flatten_sensors(self, device: dict[str, Any]) -> list[dict[str, Any]]:
        """Recursively find all sensors."""
        if not device[LHM_CHILDREN]:
            return [device] if LHM_SENSOR_ID in device else []
        return [sensor for child in device[LHM_CHILDREN] for sensor in self._flatten_sensors(child)]

    def _convert_to_seconds(self, timespan: str | None) -> str | None:
        """Convert formatted timespan to seconds."""
        if timespan is None:
            return None

        hours_minutes_seconds = timespan.split(":")

        if len(hours_minutes_seconds) != 3:
            return None

        try:
            hours = int(hours_minutes_seconds[0])
            minutes = int(hours_minutes_seconds[1])
            seconds = int(hours_minutes_seconds[2])

            converted_to_seconds = hours * 3600 + minutes * 60 + seconds
            return str(converted_to_seconds)
        except ValueError:
            return None
