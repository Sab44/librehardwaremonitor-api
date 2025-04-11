import unittest
from typing import Any

from librehardwaremonitor_api import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser, LHM_CHILDREN
import json

class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.data_json: dict[str, Any] = {}
        with open('librehardwaremonitor.json') as f:
            self.data_json: dict[str, Any] = json.load(f)
        self.parser = LibreHardwareMonitorParser()


    def test_device_without_children_or_sensor_id_is_ignored(self) -> None:
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []
        expected_main_devices = [
            "AMD Ryzen 7 7800X3D",
            "NVIDIA GeForce RTX 4080 SUPER"
        ]

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_names == expected_main_devices
        assert len(set([value.device_name for value in result.sensor_data.values()])) == 2
        assert len([value for value in result.sensor_data.values() if value.device_name == "AMD Ryzen 7 7800X3D"]) == 72
        assert len([value for value in result.sensor_data.values() if value.device_name == "NVIDIA GeForce RTX 4080 SUPER"]) == 32
        assert len(result.sensor_data) == 104


    def test_error_is_raised_when_no_devices_are_available(self) -> None:
        del self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][1:]
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []

        with self.assertRaises(LibreHardwareMonitorNoDevicesError):
            result = self.parser.parse_data(self.data_json)


    def test_lhm_json_is_parsed_correctly(self) -> None:
        expected_main_devices = [
            "MSI MAG B650M MORTAR WIFI (MS-7D76)",
            "AMD Ryzen 7 7800X3D",
            "NVIDIA GeForce RTX 4080 SUPER"
        ]

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_names == expected_main_devices
        assert len(set([value.device_name for value in result.sensor_data.values()])) == 3
        assert len([value for value in result.sensor_data.values() if value.device_name == "MSI MAG B650M MORTAR WIFI (MS-7D76)"]) == 37
        assert len([value for value in result.sensor_data.values() if value.device_name == "AMD Ryzen 7 7800X3D"]) == 72
        assert len([value for value in result.sensor_data.values() if value.device_name == "NVIDIA GeForce RTX 4080 SUPER"]) == 32
        assert len(result.sensor_data) == 141