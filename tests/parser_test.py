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
        with open(f"{self.BASE_DIR}/librehardwaremonitor.json") as f:
            self.data_json = json.load(f)
        self.parser = LibreHardwareMonitorParser()

    def test_computer_name_is_parsed(self) -> None:
        result = self.parser.parse_data(self.data_json)
        print(result.computer_name)

        assert result.computer_name == "COMPUTER"

    def test_device_without_children_or_sensor_id_is_ignored(self) -> None:
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []
        expected_main_device_ids_and_names = {
            "amdcpu-0": "AMD Ryzen 7 7800X3D",
            "gpu-nvidia-test-0": "NVIDIA GeForce RTX 4080 SUPER",
            "battery-DELL-G8VCF6C_1": "DELL G8VCF6C",
        }

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_ids_and_names == expected_main_device_ids_and_names

        sensor_data = result.sensor_data.values()
        assert len(set([value.device_name for value in result.sensor_data.values()])) == 3
        assert sum(value.device_name == "AMD Ryzen 7 7800X3D" for value in sensor_data) == 72
        assert sum(value.device_name == "NVIDIA GeForce RTX 4080 SUPER" for value in sensor_data) == 32
        assert sum(value.device_name == "DELL G8VCF6C" for value in sensor_data) == 2
        assert len(result.sensor_data) == 106

    def test_error_is_raised_when_no_devices_with_sensors_are_available(self) -> None:
        del self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][1:]
        self.data_json[LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN][0][LHM_CHILDREN] = []

        with self.assertRaises(LibreHardwareMonitorNoDevicesError):
            _ = self.parser.parse_data(self.data_json)

    def test_lhm_json_is_parsed_correctly(self) -> None:
        expected_main_device_ids_and_names = {
            "lpc-nct6687d-0": "MSI MAG B650M MORTAR WIFI (MS-7D76)",
            "amdcpu-0": "AMD Ryzen 7 7800X3D",
            "gpu-nvidia-test-0": "NVIDIA GeForce RTX 4080 SUPER",
            "battery-DELL-G8VCF6C_1": "DELL G8VCF6C",
        }

        result = self.parser.parse_data(self.data_json)

        assert result
        assert result.main_device_ids_and_names == expected_main_device_ids_and_names

        sensor_data = result.sensor_data.values()
        assert len(set([value.device_name for value in sensor_data])) == 4
        assert sum(value.device_name == "MSI MAG B650M MORTAR WIFI (MS-7D76)" for value in sensor_data) == 37
        assert sum(value.device_name == "AMD Ryzen 7 7800X3D" for value in sensor_data) == 72
        assert sum(value.device_name == "NVIDIA GeForce RTX 4080 SUPER" for value in sensor_data) == 32
        assert sum(value.device_name == "DELL G8VCF6C" for value in sensor_data) == 2
        assert len(result.sensor_data) == 143

        assert "gpu-nvidia-0-control-1" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-control-1"].device_id == "gpu-nvidia-test-0"
        assert result.sensor_data["gpu-nvidia-0-control-1"].device_type == "NVIDIA"

        # test Throughput sensor without RawValue being available
        assert "gpu-nvidia-0-throughput-0" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].value == "100.0"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].min == "50.0"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].max == "199.3"
        assert result.sensor_data["gpu-nvidia-0-throughput-0"].unit == "MB/s"

        # test Throughput sensor with RawValue being available
        assert "gpu-nvidia-0-throughput-1" in result.sensor_data
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].value == "300.0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].min == "50.0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].max == "683250.0"
        assert result.sensor_data["gpu-nvidia-0-throughput-1"].unit == "KB/s"

        # test TimeSpan sensor without RawValue being available
        assert "battery-DELL-G8VCF6C_1-timespan-0" in result.sensor_data
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-0"].value == "7351"
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-0"].min == "2596"
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-0"].max == "43382"

        # test TimeSpan sensor with RawValue being available
        assert "battery-DELL-G8VCF6C_1-timespan-1" in result.sensor_data
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-1"].value == "3751"
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-1"].min == "2596"
        assert result.sensor_data["battery-DELL-G8VCF6C_1-timespan-1"].max == "3782"

        # test non-numerical values are converted to None
        # "-" values
        assert "lpc-nct6687d-0-control-7" in result.sensor_data
        assert result.sensor_data["lpc-nct6687d-0-control-7"].value is None
        assert result.sensor_data["lpc-nct6687d-0-control-7"].min is None
        assert result.sensor_data["lpc-nct6687d-0-control-7"].max is None
        # "NaN" values
        assert "amdcpu-0-clock-11" in result.sensor_data
        assert result.sensor_data["amdcpu-0-clock-11"].value is None
        assert result.sensor_data["amdcpu-0-clock-11"].min is None
        assert result.sensor_data["amdcpu-0-clock-11"].max is None

        device_ids = set([sensor_data.device_id for sensor_data in result.sensor_data.values()])
        assert device_ids == {
            "lpc-nct6687d-0",
            "amdcpu-0",
            "gpu-nvidia-test-0",
            "battery-DELL-G8VCF6C_1",
        }
