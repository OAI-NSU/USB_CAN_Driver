from dataclasses import dataclass
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo

@dataclass
class SerialInfo:
    port: str
    serial_num: str


def get_connected_devices() -> list[SerialInfo]:
    """
    Returns all connected devices with the following format:
    [("PORT", "SERIAL_NUM"), ... ]
    """
    devices_list: list[ListPortInfo] = serial.tools.list_ports.comports()
    if len(devices_list) == 0:  # There is no connected devices
        return []
    return [SerialInfo(device_info.device, device_info.serial_number or '')
            for device_info in devices_list]

if __name__ == '__main__':
    print(get_connected_devices())