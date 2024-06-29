from queue import Empty, Queue
from threading import Thread
import time
from loguru import logger
from serial import Serial, SerialException
import struct

from usb_can_driver.canv_structs import CAN_Transaction, IVar, CMD_Type



class LM_USB_CAN:
    def __init__(self) -> None:
        self._ser: Serial
        self.connection_status: bool = False
        self._queue: Queue[CAN_Transaction] = Queue()
        self._working_flag: bool = True
        self._thread: Thread
        self.pkt_counter = 0

    def connect(self, port: str) -> bool:
        if hasattr(self, '_ser') and self._ser.is_open:
            return True
        self._ser = Serial(port, 115200, write_timeout=2, timeout=0.5)
        self.connection_status = self._ser.is_open
        self._thread = Thread(name='USB_CAN_thread', target=self._routine,
                              daemon=True)
        self._thread.start()
        return self.connection_status

    def disconnect(self) -> None:
        if hasattr(self, '_ser') and not self._ser.is_open:
            return None
        self._working_flag = False
        self._thread.join(2)
        self.connection_status = False

    def cli(self) -> None:
        self._cli_thread = Thread(name='CLI', target=self._cli_routine,
                            daemon=True)
        self._cli_thread.start()

    @staticmethod
    def _read(ivar: IVar, d_len: int, can_num: int) -> CAN_Transaction:
        cmd: CAN_Transaction = CAN_Transaction(ivar, [], CMD_Type.READ, d_len)
        offset: int = ivar.offset
        while d_len > 0:
            packet: bytes = struct.pack('<bb', can_num, 0)
            packet += ivar.to_bytes(CMD_Type.READ)
            packet += struct.pack('<H', 8 if d_len > 8 else d_len)
            cmd.packets.append(packet)
            ivar.offset += 8
            d_len -= 8
        ivar.offset = offset
        return cmd

    def read(self, ivar: IVar, d_len: int = 0,
             can_num: int = 0) -> CAN_Transaction:
        cmd: CAN_Transaction = self._read(ivar, d_len, can_num)
        self._queue.put_nowait(cmd)
        return cmd

    @staticmethod
    def _write(ivar: IVar, data: bytes, can_num: int) -> CAN_Transaction:
        cmd: CAN_Transaction = CAN_Transaction(ivar, [], CMD_Type.WRITE,
                                               data=data)
        chunks: list[bytes] = [data[i: i + 8] for i in range(0, len(data), 8)]
        offset: int = ivar.offset
        for chunk in chunks:
            packet: bytes = struct.pack('<bb', can_num, 0)
            packet += ivar.to_bytes(CMD_Type.WRITE)
            packet += struct.pack('<H', len(chunk))
            packet += chunk
            cmd.packets.append(packet)
            ivar.offset += 8
        ivar.offset = offset
        return cmd

    def write(self, ivar: IVar, data: bytes = b'',
              can_num: int = 0) -> CAN_Transaction:
        packets: CAN_Transaction = self._write(ivar, data, can_num)
        self._queue.put_nowait(packets)
        return packets

    def _routine(self) -> None:
        while self._working_flag:
            try:
                next_cmd: CAN_Transaction = self._queue.get_nowait()
                logger.debug('Sending:')
                buffer: bytes = b''
                for packet in next_cmd.packets:
                    self._ser.write(packet)
                    logger.debug(f'Packet type: {next_cmd.cmd_type}\n'\
                                 f'Data: {packet.hex(" ", 2).upper()}')
                    rx_data: bytes | None = self._ser.read(16)

                    if next_cmd.cmd_type == CMD_Type.READ:
                        if rx_data:
                            buffer += rx_data[8:]
                            logger.info(rx_data.hex(" ", 2).upper())

                        else:
                            logger.error(f'Timeout for packet: {packet.hex(" ", 2).upper()}')
                if buffer:
                    if len(buffer) == next_cmd.d_len:
                        self.pkt_counter += 1
                        logger.debug(buffer.hex(" ").upper())
                    else:
                        logger.warning('Incorrect data len')
            except Empty:
                try:
                    rx_data: bytes | None = self._ser.read_all()
                except SerialException as err:
                    logger.error(err)
                    logger.info('Please restart app')
                    return None
                if rx_data:
                    logger.debug(f'got unexpected data: {rx_data.hex(" ").upper()}')
            except SerialException as err:
                logger.error(err)
                logger.info('Please restart app')
                return None
            time.sleep(0.001)

    def _cli_routine(self) -> None:
        while self._working_flag:
            try:
                data: str = input('> ')
                if data == 'p':
                    print(self.pkt_counter)
            except (SyntaxError, ValueError, EOFError) as err:
                print(err)
