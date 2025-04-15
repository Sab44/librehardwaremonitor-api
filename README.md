# LibreHardwareMonitor API Client
A Python library for interacting with the LibreHardwareMonitor API.

## Overview
This library provides a simple interface for fetching data from the API provided by the inbuilt LibreHardwareMonitor web server.

## Methods
The library provides two callable methods to fetch data from your Libre Hardware Monitor instance:

* `get_data`: Returns a `LibreHardwareMonitorData` object containing all sensor data.
* `get_main_hardware_devices`: Returns a `list` containing all names of main hardware devices.

`LibreHardwareMonitorData` has 1 property with the following structure:
```
LibreHardwareMonitorData(
    sensor_data: dict[str, LibreHardwareMonitorSensorData] 
    # for example 
    # {
    #     "amdcpu-0-power-0": {
    #         "name": Package Power", 
    #         "value": "25,6", 
    #         "min": "25,2", 
    #         "max": "76,4", 
    #         "unit": "W", 
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
    print(lhm_data.sensor_data)
    
    main_hardware_devices = await client.get_main_hardware_devices()
    print(main_hardware_devices)

asyncio.run(main())
```

## TODO
* implement basic auth
