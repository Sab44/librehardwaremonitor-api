# LibreHardwareMonitor API Client
A Python library for interacting with the [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) API.

## Overview
This library provides a simple interface for fetching data from the API provided by the inbuilt LibreHardwareMonitor web server.

## Methods
The library provides one callable method:

* `get_data`: Returns a `LibreHardwareMonitorData` object containing main device names and all sensor data from your Libre Hardware Monitor instance.

`LibreHardwareMonitorData` has 2 properties with the following structure:
```
LibreHardwareMonitorData(
    main_device_ids_and_names: dict[DeviceId, DeviceName]
    # for example:
    # {
    #     "amdcpu-0": "AMD Ryzen 7 7800X3D",
    #     "gpu-nvidia-0": "NVIDIA GeForce RTX 4080 SUPER"
    # }
    # the dictionary keys represent a unique device id.
    
    sensor_data: dict[str, LibreHardwareMonitorSensorData]
    # for example
    # {
    #     "amdcpu-0-power-0": {
    #         "name": Package Power",
    #         "value": "25,6",
    #         "min": "25,2",
    #         "max": "76,4",
    #         "unit": "W",
    #         "device_id": "amdcpu-0",
    #         "device_name": "AMD Ryzen 7 7800X3D",
    #         "device_type": "CPU",
    #         "sensor_id": "amdcpu-0-power-0"
    #     },
    #     "amdcpu-0-power-1" : { ... },
    #     ...
    # }
    # the dictionary keys represent a unique sensor id.
)
```



## Installation
To install the library, run the following command:
```bash
pip install librehardwaremonitor-api
```

## Usage
```
import asyncio
from librehardwaremonitor_api import LibreHardwareMonitorClient

async def main():
    client = LibreHardwareMonitorClient("<HOSTNAME OR IP ADDRESS>", <PORT>)
    
    lhm_data = await client.get_data()
    print(lhm_data.main_device_ids_and_names)
    print(lhm_data.sensor_data)

asyncio.run(main())
```

## TODO
* implement basic auth
