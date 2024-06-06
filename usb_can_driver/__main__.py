

import time
from loguru import logger
from usb_can_driver.canv_structs import IVar
from usb_can_driver.usb_can import LM_USB_CAN


if __name__ == '__main__':
    # print(LM_USB_CAN._write(IVar(5, 2, 0x40), bytes(range(25)), 0))
    # print(LM_USB_CAN._read(IVar(5, 2, 0), 12, 0))
    device = LM_USB_CAN()
    logger.remove()
    if device.connect('COM24'):
        t = time.time()
        for _ in range(100):
            device.read(IVar(6, 5, 0), 128)
        while device.pkt_counter != 100:
            delta = time.time() - t
            time.sleep(0.001)
        print(delta)
        # device.write(IVar(6, 4, 0x40), bytes([2]))
        # device.write(IVar(6, 2, 0x10), b'\x01')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            device.disconnect()
            print('Shutting down')
