"""pymodbus Modbus RTU master: reads 3 registers at 0x6B from slave 0x11, then an absent address."""
import os
import sys

import pymodbus
from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient

port = sys.argv[1]
print("pymodbus", pymodbus.__version__)
c = ModbusSerialClient(port, framer=FramerType.RTU, baudrate=int(os.environ.get("BAUD", "19200")), parity="N", stopbits=2, timeout=1, retries=0)
c.connect()
for adr, n in [(0x6B, 3), (0x0FA0, 1)]:
    try:
        r = c.read_holding_registers(adr, count=n, slave=0x11)
        print(f"read_holding_registers({adr:#06x}, count={n}) ->", r)
        if not r.isError():
            print("  registers =", [f"{v:#06x}" for v in r.registers])
        else:
            print(f"  function_code = {r.function_code:#04x}, exception_code = {r.exception_code:#04x}")
    except Exception as e:  # noqa: BLE001
        print(f"read_holding_registers({adr:#06x}, count={n}) -> {type(e).__name__}: {e}")
c.close()
