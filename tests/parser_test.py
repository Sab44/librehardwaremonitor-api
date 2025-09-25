import json
import unittest
from pathlib import Path
from typing import Any

from librehardwaremonitor_api import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.parser import LHM_CHILDREN
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser


class TestParser(unittest.TestCase):

    BASE_DIR = Path(__file__).absolute().parent

    def setUp(self) -> None:
        self.data_json: dict[str, Any] = {}
        with open(f'{self.BASE_DIR}/librehardwaremonitor.json') as f:
            self.data_json: dict[str, Any] = json.load(f)
        self.parser = LibreHardwareMonitorParser()


    def test_device_without_children_or_sensor_id_is_ignored(self) -> None:
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []
        expected_main_device_ids_and_names = {
            "amdcpu-0": "AMD Ryzen 7 7800X3D",
            "gpu-nvidia-test-0": "NVIDIA GeForce RTX 4080 SUPER"
        }

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_ids_and_names == expected_main_device_ids_and_names
        assert len(set([value.device_name for value in result.sensor_data.values()])) == 2
        assert len([value for value in result.sensor_data.values() if value.device_name == "AMD Ryzen 7 7800X3D"]) == 72
        assert len([value for value in result.sensor_data.values() if value.device_name == "NVIDIA GeForce RTX 4080 SUPER"]) == 32
        assert len(result.sensor_data) == 104


    def test_error_is_raised_when_no_devices_with_sensors_are_available(self) -> None:
        del self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][1:]
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []

        with self.assertRaises(LibreHardwareMonitorNoDevicesError):
            _ = self.parser.parse_data(self.data_json)


    def test_lhm_json_is_parsed_correctly(self) -> None:
        expected_main_device_ids_and_names = {
            "lpc-nct6687d-0": "MSI MAG B650M MORTAR WIFI (MS-7D76)",
            "amdcpu-0": "AMD Ryzen 7 7800X3D",
            "gpu-nvidia-test-0": "NVIDIA GeForce RTX 4080 SUPER"
        }

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_ids_and_names == expected_main_device_ids_and_names
        assert len(set([value.device_name for value in result.sensor_data.values()])) == 3
        assert len([value for value in result.sensor_data.values() if value.device_name == "MSI MAG B650M MORTAR WIFI (MS-7D76)"]) == 37
        assert len([value for value in result.sensor_data.values() if value.device_name == "AMD Ryzen 7 7800X3D"]) == 72
        assert len([value for value in result.sensor_data.values() if value.device_name == "NVIDIA GeForce RTX 4080 SUPER"]) == 32
        assert len(result.sensor_data) == 141

        assert "gpu-nvidia-0-control-1" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-control-1"].device_id == "gpu-nvidia-test-0"
        assert result.sensor_data["gpu-nvidia-0-control-1"].device_type == "NVIDIA"

        # test Throughput sensor without RawValue being available
        assert "gpu-nvidia-0-throughput-0" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].value == "100,0"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].min == "50,0"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].max == "199,3"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].unit == "MB/s"

        # test Throughput sensor with RawValue being available
        assert "gpu-nvidia-0-throughput-1" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].value == "300,0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].min == "50,0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].max == "683250,0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].unit == "KB/s"

        device_ids = set([sensor_data.device_id for sensor_data in result.sensor_data.values()])
        assert device_ids == {"lpc-nct6687d-0", "amdcpu-0", "gpu-nvidia-test-0"}