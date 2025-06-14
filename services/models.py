from typing import NamedTuple

class DeviceInfo(NamedTuple):
    address: str
    serial_number: bytes
    device_name: str