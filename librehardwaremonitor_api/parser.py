from typing import Any

from librehardwaremonitor_api.errors import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.model import LibreHardwareMonitorSensorData, LibreHardwareMonitorData

LHM_CHILDREN = "Children"
LHM_DEVICE_TYPE = "ImageURL"
LHM_MIN = "Min"
LHM_MAX = "Max"
LHM_NAME = "Text"
LHM_SENSOR_ID = "SensorId"
LHM_TYPE = "Type"
LHM_VALUE = "Value"

class LibreHardwareMonitorParser:

    def parse_data(self, lhm_data: dict[str, Any]) -> LibreHardwareMonitorData:
        """Get data from all sensors across all devices."""
        main_devices = lhm_data[LHM_CHILDREN][0][LHM_CHILDREN]

        sensor_data: dict[str, LibreHardwareMonitorSensorData] = {}
        for main_device in main_devices:
            sensors_for_device = self._parse_sensor_data(main_device)

            for sensor in sensors_for_device:
                sensor_data[sensor.sensor_id] = sensor

        if not sensor_data:
            raise LibreHardwareMonitorNoDevicesError from None

        return LibreHardwareMonitorData(sensor_data=sensor_data)


    def _parse_sensor_data(self, main_device: dict[str, Any]) -> list[LibreHardwareMonitorSensorData]:
        """Parse all sensors from a given device."""
        device_type = self._parse_device_type(main_device)

        sensor_data_for_device: list[LibreHardwareMonitorSensorData] = []
        all_sensors_for_device = self._flatten_sensors(main_device)
        for sensor in all_sensors_for_device:
            sensor_id = "-".join(sensor[LHM_SENSOR_ID].split("/")[1:]).replace(
                "%", ""
            )

            unit = None
            if " " in sensor[LHM_VALUE]:
                unit = sensor[LHM_VALUE].split(" ")[1]

            sensor_data = LibreHardwareMonitorSensorData(
                name=f"{sensor[LHM_NAME]} {sensor[LHM_TYPE]}",
                value=sensor[LHM_VALUE].split(" ")[0],
                min=sensor[LHM_MIN].split(" ")[0],
                max=sensor[LHM_MAX].split(" ")[0],
                unit=unit,
                device_name=main_device[LHM_NAME],
                device_type=device_type,
                sensor_id=sensor_id,
            )
            sensor_data_for_device.append(sensor_data)

        return sensor_data_for_device


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


    def parse_main_hardware_device_names(self, lhm_data: dict[str, Any]) -> list[str]:
        """Get names of all main hardware devices (CPU, GPU, SSD...) exposed by LHM."""
        main_devices = lhm_data[LHM_CHILDREN][0][LHM_CHILDREN]

        if not main_devices:
            raise LibreHardwareMonitorNoDevicesError from None

        return [main_device[LHM_NAME] for main_device in main_devices]