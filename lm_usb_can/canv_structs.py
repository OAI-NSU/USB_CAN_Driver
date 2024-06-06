from dataclasses import dataclass
from enum import Enum
from typing import Type


class CANV_VAR_ID(Enum):
    CODE_PTR = 0  # Read only. для STM32 0x8000000
    DATA_PTR = 1  # Read only. для STM32 0x20000000
    CMD = 2  # Read/Write. регистры для разных команд – разные. Команда и статус должны иметь одинаковое смещение
    CMD_STATUS = 3  # Read only. регистры для разных команд – разные. Команда и статус должны иметь одинаковое смещение
    REGISTER = 4  # Read/Write.
    CONDITION_VAR = 5  # Read only. первыми располагаются регистры, входящие в состав маяка
    PARAMETERS = 6  # Read/Write.
    DATA_ARRAY_1 = 7  # для БРК - это память FRAM
    DATA_ARRAY_2 = 8  # для СОП - снимки
    DATA_ARRAY_3 = 9
    DATA_ARRAY_4 = 10
    DATA_ARRAY_5 = 11
    DATA_ARRAY_6 = 12
    DATA_ARRAY_7 = 13
    BOOTLOADER = 14
    BROADCAST = 15  # Write only. совместно с DevID=15 для широковещательной посылки


class CANV_DEV_ID(Enum):
    COMMAND_LINE_RADIO_MAIN = 1
    COMMAND_LINE_RADIO_RESERVE = 2
    POWER_SUPPLY_SYSTEM = 3
    ORIENTATION_SYSTEM_MAIN = 4
    ORIENTATION_SYSTEM_RESERVE = 5
    LINKING_MODULE = 6
    SUBSYSTEM_7 = 7
    SUBSYSTEM_8 = 8
    SUBSYSTEM_9 = 9
    SUBSYSTEM_10 = 10
    SUBSYSTEM_11 = 11
    SUBSYSTEM_12 = 12
    SUBSYSTEM_13 = 13

class CMD_Type(Enum):
    WRITE = 0
    READ = 1

@dataclass
class IVar:
    dev_id: CANV_DEV_ID | int
    var_id: CANV_VAR_ID | int
    offset: int

    def _validate(self, val, target_class: Type[Enum]) -> int:
        if isinstance(val, target_class):
            validated = val.value
        elif 1 <= val <= 15:
            validated = val
        else:
            raise ValueError(f'Incorrect DevID value: {val}')
        return validated

    def to_bytes(self, mode: CMD_Type) -> bytes:
        _dev_id_val: int = self._validate(self.dev_id, CANV_DEV_ID)
        _var_id_val: int = self._validate(self.var_id, CANV_VAR_ID)

        _dev_id: int = _dev_id_val << 28
        _var_id: int = _var_id_val << 24
        _offset: int = self.offset << 3
        return (_dev_id | _var_id | _offset | (mode.value << 1)).to_bytes(4, 'little')

    def __str__(self) -> str:
        return f'DEV_ID: {self.dev_id}\nVAR_ID: {self.var_id}\n'\
               f'Offset: {self.offset}'

    @staticmethod
    def parse(data: bytes) -> "IVar":
        val: int = int.from_bytes(data, 'little')
        dev_id: int = (val >> 28)
        var_id: int = (val >> 24) & 0x0F
        offset: int = (val >> 3) & 0xFFFFF
        return IVar(CANV_DEV_ID(dev_id), CANV_VAR_ID(var_id), offset)

@dataclass
class CAN_Transaction:
    ivar: IVar
    packets: list[bytes]
    cmd_type: CMD_Type
    d_len: int = 0
    data: bytes = b''

    def __str__(self) -> str:
        data_repr: list[str] = [f'{packet.hex(" ", 2).upper()}'
                                for packet in self.packets]
        result_str: str = f'Packet type: {self.cmd_type}\n{self.ivar}\n'\
                          f'Hex data: {data_repr}\n'
        return result_str


if __name__ == '__main__':
    ivar = IVar(1, 5, 119)
    print(ivar)
    print(IVar.parse(ivar.to_bytes(CMD_Type.READ)))