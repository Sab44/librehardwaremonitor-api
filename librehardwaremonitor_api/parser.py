import re
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
        main_device_ids_and_names: dict[DeviceId, DeviceName] = {}

        main_devices: list[dict[str, Any]] = lhm_data[LHM_CHILDREN][0][LHM_CHILDREN]

        sensors_data: dict[str, LibreHardwareMonitorSensorData] = {}
        for main_device in main_devices:
            sensor_data_for_device = self._parse_sensor_data(main_device)

            for sensor_data in sensor_data_for_device:
                sensors_data[sensor_data.sensor_id] = sensor_data
                main_device_ids_and_names[DeviceId(sensor_data.device_id)] = DeviceName(main_device[LHM_NAME])

        if not sensors_data:
            raise LibreHardwareMonitorNoDevicesError from None

        return LibreHardwareMonitorData(
            main_device_ids_and_names=main_device_ids_and_names,
            sensor_data=sensors_data
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

            value: str = sensor[LHM_VALUE].split(" ")[0]
            min: str = sensor[LHM_MIN].split(" ")[0]
            max: str = sensor[LHM_MAX].split(" ")[0]

            unit = None
            if " " in sensor[LHM_VALUE]:
                unit = sensor[LHM_VALUE].split(" ")[1]

            if type == "Throughput":
                if raw_value := sensor.get(LHM_RAW_VALUE):
                    value = raw_value.split(" ")[0]
                    min = sensor[LHM_RAW_MIN].split(" ")[0]
                    max = sensor[LHM_RAW_MAX].split(" ")[0]

                    if "," in value:
                        value = f"{(float(value.replace(',', '.')) / 1024):.1f}".replace('.', ',')
                        min = f"{(float(min.replace(',', '.')) / 1024):.1f}".replace('.', ',')
                        max = f"{(float(max.replace(',', '.')) / 1024):.1f}".replace('.', ',')
                    else:
                        value = f"{(float(value) / 1024):.1f}"
                        min = f"{(float(min) / 1024):.1f}"
                        max = f"{(float(max) / 1024):.1f}"

                    unit = "KB/s"

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
        return [
            sensor
            for child in device[LHM_CHILDREN]
            for sensor in self._flatten_sensors(child)
        ]