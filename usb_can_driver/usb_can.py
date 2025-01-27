import asyncio
import time
from serial_client import AioSerialClient
import struct

from usb_can_driver.canv_structs import CAN_Transaction, IVar


class USB_CAN_Driver:
    def __init__(self) -> None:
        self._ser = AioSerialClient()

    def connect(self, port: str) -> bool:
        return self._ser.connect(port)

    def disconnect(self) -> None:
        return self._ser.disconnect()

    @staticmethod
    def _read(ivar: IVar, d_len: int, can_num: int) -> CAN_Transaction:
        cmd: CAN_Transaction = CAN_Transaction(ivar, [], d_len)
        offset: int = ivar.offset
        while d_len > 0:
            packet: bytes = struct.pack('<bb', can_num, 0)
            packet += ivar.to_bytes(True)
            packet += struct.pack('<H', 8 if d_len > 8 else d_len)
            cmd.packets.append(packet)
            ivar.offset += 8
            d_len -= 8
        ivar.offset = offset
        return cmd

    async def read(self, ivar: IVar, d_len: int = 0,
                   can_num: int = 0) -> bytes:
        cmd: CAN_Transaction = self._read(ivar, d_len, can_num)
        return await self._transaction(cmd)

    @staticmethod
    def _write(ivar: IVar, data: bytes, can_num: int) -> CAN_Transaction:
        cmd: CAN_Transaction = CAN_Transaction(ivar, [], data=data)
        chunks: list[bytes] = [data[i: i + 8] for i in range(0, len(data), 8)]
        offset: int = ivar.offset
        for chunk in chunks:
            packet: bytes = struct.pack('<bb', can_num, 0)
            packet += ivar.to_bytes()
            packet += struct.pack('<H', len(chunk))
            packet += chunk
            cmd.packets.append(packet)
            ivar.offset += 8
        ivar.offset = offset
        return cmd

    async def _transaction(self, cmd: CAN_Transaction) -> bytes:
        rx_data: bytes = b''
        for packet in cmd.packets:
            result: bytes = await self._ser.transaction(packet, 16, 1)
            rx_data += result[8:]
            # await asyncio.sleep(0.0001)
        return rx_data

    async def write(self, ivar: IVar, data: bytes = b'',
              can_num: int = 0) -> bytes:
        cmd: CAN_Transaction = self._write(ivar, data, can_num)
        return await self._transaction(cmd)


async def main():
    start = time.time()
    for _ in range(10):
        print((await lm.read(IVar(4, 5, 40), 128)).hex(' ').upper())
    print(f'{time.time() - start:.3f}')


if __name__ == '__main__':
    lm = USB_CAN_Driver()
    lm.connect('COM16')
    asyncio.run(main())