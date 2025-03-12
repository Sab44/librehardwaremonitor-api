# LibreHardwareMonitor API Client
A Python library for interacting with the LibreHardwareMonitor API.

## Overview
This library provides a simple interface for fetching data from the API provided by the inbuilt LibreHardwareMonitor web server.

## Methods
The library provides two callable methods:

* `get_data_json`: Returns the unmodified `data.json` response from the LibreHardwareMonitor API as dict.
* `get_hardware_device_names`: Returns a list of all hardware device names in the computer.

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
    
    data_json = await client.get_data_json()
    print(data_json)
    
    device_names = await client.get_hardware_device_names()
    print(device_names)

asyncio.run(main())
```

## TODO
* implement basic auth
