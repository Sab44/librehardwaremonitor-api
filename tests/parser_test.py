import json
from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion

from librehardwaremonitor_api import LibreHardwareMonitorNoDevicesError
from librehardwaremonitor_api.model import DeviceId
from librehardwaremonitor_api.model import LibreHardwareMonitorVersion
from librehardwaremonitor_api.parser import LHM_CHILDREN
from librehardwaremonitor_api.parser import LHM_HARDWARE_ID
from librehardwaremonitor_api.parser import LHM_MAX
from librehardwaremonitor_api.parser import LHM_MIN
from librehardwaremonitor_api.parser import LHM_RAW_MAX
from librehardwaremonitor_api.parser import LHM_RAW_MIN
from librehardwaremonitor_api.parser import LHM_RAW_VALUE
from librehardwaremonitor_api.parser import LHM_SENSOR_ID
from librehardwaremonitor_api.parser import LHM_TYPE
from librehardwaremonitor_api.parser import LHM_VALUE
from librehardwaremonitor_api.parser import LHM_VERSION
from librehardwaremonitor_api.parser import LibreHardwareMonitorParser

BASE_DIR = Path(__file__).absolute().parent
# LHM 0.9.6 provides raw values as formatted strings
LHM_0_9_6_JSON = "fixtures/librehardwaremonitor_0.9.6.json"
# LHM 0.9.7 provides its version and raw values as numbers, data sensors in bytes
LHM_0_9_7_JSON = "fixtures/librehardwaremonitor_0.9.7_nightly.json"


@pytest.fixture
def parser() -> LibreHardwareMonitorParser:
    return LibreHardwareMonitorParser()


@pytest.fixture(params=[LHM_0_9_6_JSON, LHM_0_9_7_JSON])
def lhm_json(request: pytest.FixtureRequest) -> dict[str, Any]:
    return _load_json(request.param)


@pytest.fixture
def lhm_json_0_9_7() -> dict[str, Any]:
    return _load_json(LHM_0_9_7_JSON)


def test_lhm_json_is_parsed_correctly(
    parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any], snapshot: SnapshotAssertion
) -> None:
    assert parser.parse_data(lhm_json) == snapshot


def test_lhm_json_readings_are_distinct(parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]) -> None:
    # Ensures the snapshot detects min, value and max being mixed up
    result = parser.parse_data(lhm_json)

    for sensor_data in result.sensor_data.values():
        if sensor_data.value is not None:
            assert sensor_data.min != sensor_data.value != sensor_data.max, sensor_data.sensor_id


def test_device_without_children_or_sensor_id_is_ignored(
    parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]
) -> None:
    motherboard = lhm_json[LHM_CHILDREN][0][LHM_CHILDREN][0]
    motherboard[LHM_CHILDREN] = []

    result = parser.parse_data(lhm_json)

    assert "motherboard" not in result.main_device_ids_and_names
    assert not [sensor for sensor in result.sensor_data.values() if sensor.device_id == "motherboard"]


def test_error_is_raised_when_no_devices_with_sensors_are_available(
    parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]
) -> None:
    for main_device in lhm_json[LHM_CHILDREN][0][LHM_CHILDREN]:
        main_device[LHM_CHILDREN] = []

    with pytest.raises(LibreHardwareMonitorNoDevicesError):
        parser.parse_data(lhm_json)


def test_unknown_type_is_handled(parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]) -> None:
    _find_sensor(lhm_json, "/amdcpu/0/current/1")[LHM_TYPE] = "TestUnknownType"

    result = parser.parse_data(lhm_json)

    assert result.sensor_data["amdcpu-0-current-1"].type is None
    assert result.sensor_data["amdcpu-0-current-1"].name == "EDC"


def test_nan_values_are_parsed_as_none(parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]) -> None:
    _find_sensor(lhm_json, "/amdcpu/0/clock/21").update(
        {LHM_MIN: "NaN MHz", LHM_VALUE: "NaN MHz", LHM_MAX: "NaN MHz"}
    )

    result = parser.parse_data(lhm_json)

    sensor_data = result.sensor_data["amdcpu-0-clock-21"]
    assert sensor_data.value is None
    assert sensor_data.min is None
    assert sensor_data.max is None


def test_throughput_sensor_without_raw_values_uses_formatted_values(
    parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]
) -> None:
    # LHM versions <= 0.9.4 do not provide raw values
    sensor = _find_sensor(lhm_json, "/gpu-nvidia/0/throughput/0")
    for key in (LHM_RAW_MIN, LHM_RAW_VALUE, LHM_RAW_MAX):
        del sensor[key]
    sensor.update({LHM_MIN: "50,0 MB/s", LHM_VALUE: "100,0 MB/s", LHM_MAX: "199,3 MB/s"})

    result = parser.parse_data(lhm_json)

    sensor_data = result.sensor_data["gpu-nvidia-0-throughput-0"]
    assert sensor_data.value == "100.0"
    assert sensor_data.min == "50.0"
    assert sensor_data.max == "199.3"
    assert sensor_data.unit == "MB/s"


def test_data_sensor_raw_value_of_zero_is_parsed_in_bytes(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any]
) -> None:
    _find_sensor(lhm_json_0_9_7, "/gpu-nvidia/0/data/4").update(
        {
            LHM_MIN: "0,0 KB",
            LHM_VALUE: "0,0 KB",
            LHM_MAX: "0,0 KB",
            LHM_RAW_MIN: 0,
            LHM_RAW_VALUE: 0,
            LHM_RAW_MAX: 0,
        }
    )

    result = parser.parse_data(lhm_json_0_9_7)

    sensor_data = result.sensor_data["gpu-nvidia-0-data-4"]
    assert sensor_data.value == "0.0"
    assert sensor_data.min == "0.0"
    assert sensor_data.max == "0.0"
    assert sensor_data.unit == "B"


def test_throughput_sensor_raw_value_of_zero_is_parsed_in_bytes(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any]
) -> None:
    _find_sensor(lhm_json_0_9_7, "/gpu-nvidia/0/throughput/1").update(
        {LHM_VALUE: "0,0 KB/s", LHM_RAW_VALUE: 0}
    )

    result = parser.parse_data(lhm_json_0_9_7)

    sensor_data = result.sensor_data["gpu-nvidia-0-throughput-1"]
    assert sensor_data.value == "0.0"
    assert sensor_data.min == "0.0"
    assert sensor_data.max == "1122949120.0"
    assert sensor_data.unit == "B/s"


def test_raw_values_without_min_and_max_are_parsed(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any]
) -> None:
    # LHM does not track min and max values for sensors without history
    for lhm_sensor_id in ("/gpu-nvidia/0/data/1", "/gpu-nvidia/0/throughput/1"):
        _find_sensor(lhm_json_0_9_7, lhm_sensor_id).update({LHM_RAW_MIN: None, LHM_RAW_MAX: None})

    result = parser.parse_data(lhm_json_0_9_7)

    data_sensor_data = result.sensor_data["gpu-nvidia-0-data-1"]
    assert data_sensor_data.value == "11133132800.0"
    assert data_sensor_data.min is None
    assert data_sensor_data.max is None
    assert data_sensor_data.unit == "B"

    throughput_sensor_data = result.sensor_data["gpu-nvidia-0-throughput-1"]
    assert throughput_sensor_data.value == "489999360.0"
    assert throughput_sensor_data.min is None
    assert throughput_sensor_data.max is None
    assert throughput_sensor_data.unit == "B/s"


@pytest.mark.parametrize(
    ("lhm_sensor_id", "sensor_id"),
    [
        ("/gpu-nvidia/0/data/4", "gpu-nvidia-0-data-4"),
        ("/gpu-nvidia/0/throughput/1", "gpu-nvidia-0-throughput-1"),
    ],
)
def test_sensor_without_value_is_parsed(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any], lhm_sensor_id: str, sensor_id: str
) -> None:
    _find_sensor(lhm_json_0_9_7, lhm_sensor_id).update(
        {
            LHM_MIN: "-",
            LHM_VALUE: "-",
            LHM_MAX: "-",
            LHM_RAW_MIN: None,
            LHM_RAW_VALUE: None,
            LHM_RAW_MAX: None,
        }
    )

    result = parser.parse_data(lhm_json_0_9_7)

    sensor_data = result.sensor_data[sensor_id]
    assert sensor_data.value is None
    assert sensor_data.min is None
    assert sensor_data.max is None


def test_battery_sensors_are_parsed(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any]
) -> None:
    lhm_json_0_9_7[LHM_CHILDREN][0][LHM_CHILDREN].append(
        {
            "id": 1000,
            "Text": "DELL G8VCF6C",
            "Min": "",
            "Value": "",
            "Max": "",
            "HardwareId": "/battery/DELL-G8VCF6C_1",
            "ImageURL": "images_icon/battery.png",
            "Children": [
                # Formatted values are converted when raw values are not available
                _create_sensor(
                    "/battery/DELL-G8VCF6C_1/timespan/0",
                    "TimeSpan",
                    "Remaining Time (Estimated)",
                    ("0:43:16", "2:02:31", "12:03:02"),
                ),
                # Formatted values are ignored when raw values are available
                _create_sensor(
                    "/battery/DELL-G8VCF6C_1/timespan/1",
                    "TimeSpan",
                    "Remaining Time",
                    ("-", "-", "-"),
                    (2596, 3751, 3782),
                ),
                _create_sensor(
                    "/battery/DELL-G8VCF6C_1/energy/0",
                    "Energy",
                    "Remaining Capacity",
                    ("22823 mWh", "23012 mWh", "23864 mWh"),
                    (22823, 23012, 23864),
                ),
            ],
        }
    )

    result = parser.parse_data(lhm_json_0_9_7)

    assert result.main_device_ids_and_names[DeviceId("battery-DELL-G8VCF6C_1")] == "DELL G8VCF6C"

    # "TimeSpan" types are parsed in seconds and get mapped to "Time" suffix (not appended if contained in name)
    remaining_time_estimated = result.sensor_data["battery-DELL-G8VCF6C_1-timespan-0"]
    assert remaining_time_estimated.name == "Remaining Time (Estimated)"
    assert remaining_time_estimated.value == "7351"
    assert remaining_time_estimated.min == "2596"
    assert remaining_time_estimated.max == "43382"
    assert remaining_time_estimated.unit == "s"

    remaining_time = result.sensor_data["battery-DELL-G8VCF6C_1-timespan-1"]
    assert remaining_time.value == "3751"
    assert remaining_time.min == "2596"
    assert remaining_time.max == "3782"
    assert remaining_time.unit == "s"

    # "Energy" types get mapped to "Capacity" suffix (not appended if contained in name)
    remaining_capacity = result.sensor_data["battery-DELL-G8VCF6C_1-energy-0"]
    assert remaining_capacity.name == "Remaining Capacity"
    assert remaining_capacity.value == "23012"
    assert remaining_capacity.unit == "mWh"


@pytest.mark.parametrize("version", ["some.invalid.version.syntax", "v1.3.4", "0.9.7.1", "1.14.2rc1"])
def test_invalid_version_syntax_is_parsed_to_fallback_version(
    parser: LibreHardwareMonitorParser, lhm_json_0_9_7: dict[str, Any], version: str
) -> None:
    lhm_json_0_9_7[LHM_VERSION] = version

    result = parser.parse_data(lhm_json_0_9_7)

    assert result.version == LibreHardwareMonitorVersion(0, 0, 0)
    assert str(result.version) == "0.0.0"


def test_deprecated_version_is_set(parser: LibreHardwareMonitorParser, lhm_json: dict[str, Any]) -> None:
    # LHM versions <= 0.9.4 do not provide hardware ids, so the device id is parsed from the sensor id
    lhm_json[LHM_CHILDREN][0][LHM_CHILDREN][0].pop(LHM_HARDWARE_ID)

    result = parser.parse_data(lhm_json)

    assert result.is_deprecated_version
    assert result.sensor_data["lpc-nct6687d-0-voltage-0"].device_id == "lpc-nct6687d-0"


def _load_json(file_name: str) -> dict[str, Any]:
    with open(BASE_DIR / file_name) as f:
        data_json: dict[str, Any] = json.load(f)
    return data_json


def _find_sensor(lhm_json: dict[str, Any], lhm_sensor_id: str) -> dict[str, Any]:
    nodes = [lhm_json]
    while nodes:
        node = nodes.pop()
        if node.get(LHM_SENSOR_ID) == lhm_sensor_id:
            return node
        nodes.extend(node[LHM_CHILDREN])
    raise KeyError(lhm_sensor_id)


def _create_sensor(
    lhm_sensor_id: str,
    sensor_type: str,
    name: str,
    readings: tuple[str, str, str],
    raw_readings: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    sensor: dict[str, Any] = {
        "id": 1001,
        "Text": name,
        "Min": readings[0],
        "Value": readings[1],
        "Max": readings[2],
        "SensorId": lhm_sensor_id,
        "Type": sensor_type,
    }
    if raw_readings is not None:
        sensor.update({"RawMin": raw_readings[0], "RawValue": raw_readings[1], "RawMax": raw_readings[2]})
    sensor.update({"ImageURL": "images/transparent.png", "Children": []})
    return sensor
