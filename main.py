#!/usr/bin/env python3

from devices.cisco_ios_device import CiscoBasic
import os

if __name__ == "__main__":
    sw1 = {
        "host": "10.100.100.2",
        "device_type": os.environ["SDN_DEVICE_TYPE"],
        "username": os.environ["SDN_USERNAME"],
        "password": os.environ["SDN_PASSWORD"],
        "secret": os.environ["SDN_SECRET"],
    }

    with CiscoBasic(**sw1) as conn:
        output = conn.hostname
        print(output)
