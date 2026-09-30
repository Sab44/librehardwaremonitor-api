from enum import StrEnum


# This is a mirror of enum SensorType defined in
# https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/ISensor.cs
class SensorType(StrEnum):
    VOLTAGE = "Voltage"  # V
    CURRENT = "Current"  # A
    POWER = "Power"  # W
    CLOCK = "Clock"  # MHz
    TEMPERATURE = "Temperature"  # °C
    LOAD = "Load"  # %
    FREQUENCY = "Frequency"  # Hz
    FAN = "Fan"  # RPM
    FLOW = "Flow"  # L/h
    CONTROL = "Control"  # %
    LEVEL = "Level"  # %
    FACTOR = "Factor"  # 1
    DATA = "Data"  # B, LHM versions <= 0.9.6: GB = 2^30 Bytes
    SMALL_DATA = "SmallData"  # MB = 2^20 Bytes, LHM versions <= 0.9.6 only, merged into Data afterwards
    THROUGHPUT = "Throughput"  # B/s
    TIMESPAN = "TimeSpan"  # Seconds
    TIMING = "Timing"  # ns
    ENERGY = "Energy"  # milliwatt-hour (mWh)
    NOISE = "Noise"  # dBA
    CONDUCTIVITY = "Conductivity"  # µS/cm
    HUMIDITY = "Humidity"  # %
