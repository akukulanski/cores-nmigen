from nmigen_cocotb import run
from cores.axi_lite import AxiLiteDevice
import random

try:
    import cocotb
    from cocotb.triggers import Timer, RisingEdge, FallingEdge, Edge, Event
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
    from cocotb.result import ReturnValue, SimFailure
    from cocotb.binary import BinaryValue
    from cocotb.drivers.amba import AXI4LiteMaster
    from cocotb.drivers.amba import AXIProtocolError
    from .interfaces import *
except:
    pass


# name, dir, addr, internal_fields (size, offset)
regs_rw = [('reg_rw_1', 'rw', 0x00000004, [('field_1', 32,  0),]),
           ('reg_rw_2', 'rw', 0x00000008, [('field_2', 32,  0),]),
           ('reg_rw_3', 'rw', 0x0000000C, [('field_3', 32,  0),]),
           ('reg_rw_4', 'rw', 0x00000010, [('field_4', 32,  0),]),
           ('reg_rw_5', 'rw', 0x00000014, [('field_5', 32,  0),]),
           ('reg_rw_6', 'rw', 0x00000018, [('field_6', 32,  0),]),
           ('reg_rw_6', 'rw', 0x0000001C, [('field_7', 32,  0),]),
           ('reg_rw_7', 'rw', 0x00000020, [('field_8', 32,  0),]),

          ]
regs_ro = [('reg_ro_1', 'ro', 0x00000000, [('field_10', 32,  0),]),
           ('reg_ro_2', 'ro', 0x00000030, [('field_20', 32,  0),]),
          ]
regs = regs_rw + regs_ro

CLK_PERIOD = 10

AXI_TYPE = 0x1       # Slave = "01" / Master = "10"
AXI_PROTOCOL = 0x1   # Lite = "001" / Full = "010" / Stream = "100
CORE_ID = 0x0FF      # Core ID
VERSION_MAJOR = 0x00 # Version major
VERSION_MINOR = 0x00 # Version minor

def get_core_id():
    core_id = (AXI_TYPE<<30) | (AXI_PROTOCOL<<27) | (CORE_ID<<16) | (VERSION_MAJOR<<8) | VERSION_MINOR
    return core_id

@cocotb.coroutine
def Reset(dut):
    dut.field_10 <= get_core_id()
    dut.rst <=  1
    yield Timer(CLK_PERIOD * 10)
    dut.rst  <= 0

@cocotb.test()
def check_data(dut):
    """
    Description:
        Test Write and Read registers through AXI4 interface
    """
    axim = AXI4LiteMaster(dut, "s_axi_", dut.clk)
    cocotb.fork(Clock(dut.clk, CLK_PERIOD).start())
    yield Reset(dut)

    value = yield axim.read(0)
    yield Timer(CLK_PERIOD * 10)
    ID = get_core_id()

    dut._log.info("Check core ID: 0x%08X" % (ID))
    assert value == ID, "Core ID doesn't match: should have been: \
                            0x%08X but was 0x%08X" % (ID, int(value))
    # if value!= ID:
    #     # Fail
    #     raise TestFailure("Core ID doesn't match: should have been: \
    #                         0x%08X but was 0x%08X" % (ID, int(value)))
    dut._log.info("ID -> OK!")

    dut._log.info("Check write/read regsters")
    INIT_ADDR = 4
    END_ADDR = 16
    for ADDRESS in [reg[2] for reg in regs_rw]:
        # DATA = random.randint(0, 2**32-1)
        addr_word = int(ADDRESS / 4)
        DATA = 0x30201000 | (addr_word << 0) | (addr_word << 4) | (addr_word << 8) | (addr_word << 12)

        #Write to the register
        yield axim.write(ADDRESS, DATA)
        yield Timer(CLK_PERIOD * 10)
        #Read back the value
        value = yield axim.read(ADDRESS)
        yield Timer(CLK_PERIOD * 10)
    
        assert value == DATA, "Register at address 0x%08X should have been: \
                              0x%08X but was 0x%08X" % (ADDRESS, DATA, int(value))
        # if value != DATA:
        #     #Fail
        #     raise TestFailure("Register at address 0x%08X should have been: \
        #                     0x%08X but was 0x%08X" % (ADDRESS, DATA, int(value)))
        dut._log.info("Address 0x{:08x}: 0x{:08x} == 0x{:08x}".format(ADDRESS, int(value), DATA))
    dut._log.info("Write/Read sequence was ok, from 0x%08X to 0x%08X address" % (INIT_ADDR, ADDRESS))


def test_axi_lite_device_old():
    core = AxiLiteDevice(addr_w=6,
                         data_w=32,
                         registers=regs)
    ports = [core.axi_lite[f] for f in core.axi_lite.fields]
    ports += [core.registers[f] for f in core.registers.fields]
    run(core, 'cores.test.test_axi_lite_old', ports=ports, vcd_file='./test_axi_lite_device_old.vcd')