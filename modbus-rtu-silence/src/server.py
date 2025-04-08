"""pymodbus Modbus RTU slave: address 0x11, registers 0x6B..0x6D = 0x022B, 0x0000, 0x0064.

The holding register block covers only 0x6B..0x6D: any other address fails the
datastore range check (validate) and the slave answers exception 02.
The log shows the time in ms since start, not the wall clock.
"""
import asyncio
import logging
import sys

from pymodbus import FramerType
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartAsyncSerialServer

logging.basicConfig(format="%(relativeCreated)7.0f ms %(levelname)-5s %(module)s:%(lineno)s %(message)s")
logging.getLogger("pymodbus").setLevel(logging.DEBUG)
port = sys.argv[1]
# ModbusSlaveContext adds 1 to the protocol address, hence 0x6B + 1
hr = ModbusSequentialDataBlock(0x6B + 1, [0x022B, 0x0000, 0x0064])
context = ModbusServerContext(slaves={0x11: ModbusSlaveContext(hr=hr)}, single=False)
asyncio.run(StartAsyncSerialServer(context, framer=FramerType.RTU, port=port, baudrate=19200, parity="N", stopbits=2))
