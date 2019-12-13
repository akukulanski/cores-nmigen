from nmigen_cocotb import run
from cores.axi_lite import AxiLiteDevice
import random

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
    from .interfaces import *
except:
    pass

CLK_PERIOD_BASE = 100
random.seed()

regs_rw = [('reg_rw_1', 'rw', 0x00000000),
           ('reg_rw_2', 'rw', 0x00000004),
           ('reg_rw_3', 'rw', 0x00000008),
           ]
regs_ro = [('reg_ro_1', 'ro', 0x0000000C),
           ('reg_ro_2', 'ro', 0x00000010),
           ('reg_ro_3', 'ro', 0x00000014),]
regs = regs_rw + regs_ro

@cocotb.coroutine
def init_test(dut):
    dut.s_axi__awaddr <= 0
    dut.s_axi__awvalid <= 0
    dut.s_axi__wdata <= 0
    dut.s_axi__wstrb <= 0
    dut.s_axi__wvalid <= 0
    dut.s_axi__bready <= 0
    dut.s_axi__araddr <= 0
    dut.s_axi__arvalid <= 0
    dut.s_axi__rready <= 0
    for reg_name, reg_dir, reg_addr in regs_ro:
        setattr(dut, reg_name, 0)
    dut.rst <= 1
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)

@cocotb.coroutine
def check_rw_regs(dut):

    axi_lite = AxiLiteDriver(dut, 's_axi_', dut.clk)
    data = [random.randint(0,2**32-1) for _ in range(len(regs_rw))]

    yield init_test(dut)

    for (reg_name, reg_dir, reg_addr), value in zip(regs_rw, data):
        yield axi_lite.write_reg(reg_addr, value)

    for (reg_name, reg_dir, reg_addr), value in zip(regs_rw, data):
        assert getattr(dut, reg_name).value.integer == value, f'{hex(getattr(dut, reg_name).value.integer)} == {hex(value)}'
        rd = yield axi_lite.read_reg(reg_addr)
        assert rd == value, f'{hex(rd)} == {hex(value)}'


@cocotb.coroutine
def check_ro_regs(dut):

    axi_lite = AxiLiteDriver(dut, 's_axi_', dut.clk)
    data = [random.randint(0,2**32-1) for _ in range(len(regs_ro))]

    yield init_test(dut)

    for (reg_name, reg_dir, reg_addr), value in zip(regs_ro, data):
        setattr(dut, reg_name, value)
        yield RisingEdge(dut.clk)

    for (reg_name, reg_dir, reg_addr), value in zip(regs_ro, data):
        rd = yield axi_lite.read_reg(reg_addr)
        assert rd == value, f'{hex(rd)} == {hex(value)}'

tf_test_rw = TF(check_rw_regs)
tf_test_rw.generate_tests()

tf_test_ro = TF(check_ro_regs)
tf_test_ro.generate_tests()


def test_axi_lite_device():
    core = AxiLiteDevice(addr_w=5,
                         data_w=32,
                         registers=regs)
    ports = [core.axi_lite[f] for f in core.axi_lite.fields]
    ports += [core.registers[f] for f in core.registers.fields]
    run(core, 'cores.test.test_axi_lite', ports=ports, vcd_file='./test_axi_lite_device.vcd')