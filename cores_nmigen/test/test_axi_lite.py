from nmigen_cocotb import run
from cores_nmigen.axi_lite import AxiLiteDevice
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

# name, dir, addr, internal_fields (size, offset)
regs_rw = [('reg_rw_1', 'rw', 0x00000000, [('field_1', 32,  0),]),
           ('reg_rw_2', 'rw', 0x00000004, [('field_2',  1,  0),
                                           ('field_3', 15,  1),
                                           ('field_4', 16, 16),]),
           ('reg_rw_3', 'rw', 0x00000008, [('field_5', 32,  0),]),
          ]
regs_ro = [('reg_ro_1', 'ro', 0x0000000C, [('field_10', 32,  0),]),
           ('reg_ro_2', 'ro', 0x00000010, [('field_20',  1,  0),
                                           ('field_30', 15,  1),
                                           ('field_40', 16, 16),]),
           ('reg_ro_3', 'ro', 0x00000014, [('field_50', 32,  0),]),
          ]
regs = regs_rw + regs_ro


get_mask = lambda size, offset: (2**size-1) << offset
mask = lambda value, size, offset: (value & (2**size - 1)) << offset
unmask = lambda value, size, offset: (value >> offset) & (2**size - 1)


@cocotb.coroutine
def init_test(dut):
    dut.s_axi__AWADDR <= 0
    dut.s_axi__AWVALID <= 0
    dut.s_axi__WDATA <= 0
    dut.s_axi__WSTRB <= 0
    dut.s_axi__WVALID <= 0
    dut.s_axi__BREADY <= 0
    dut.s_axi__ARADDR <= 0
    dut.s_axi__ARVALID <= 0
    dut.s_axi__RREADY <= 0
    for r_name, r_dir, r_addr, r_fields in regs:
        if r_dir == 'ro':
            for f_name, f_size, f_offset in r_fields:
                setattr(dut, f_name, 0)
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

    for (r_name, r_dir, r_addr, r_fields), value in zip(regs_rw, data):
        yield axi_lite.write_reg(r_addr, value)

    for (r_name, r_dir, r_addr, r_fields), r_value in zip(regs_rw, data):

        rd = yield axi_lite.read_reg(r_addr)
        assert rd == r_value, f'{hex(rd)} == {hex(r_value)}'

        for f_name, f_size, f_offset in r_fields:
            f_value = getattr(dut, f_name).value.integer
            expected = unmask(r_value, f_size, f_offset)
            assert f_value == expected, f'{hex(f_value)} == {hex(expected)}'


@cocotb.coroutine
def check_ro_regs(dut):

    axi_lite = AxiLiteDriver(dut, 's_axi_', dut.clk)
    data = [random.randint(0,2**32-1) for _ in range(len(regs_ro))]

    yield init_test(dut)

    for (r_name, r_dir, r_addr, r_fields), r_value in zip(regs_ro, data):
        for f_name, f_size, f_offset in r_fields:
            setattr(dut, f_name, unmask(r_value, f_size, f_offset))
    
    yield RisingEdge(dut.clk)

    for (r_name, r_dir, r_addr, r_fields), r_value in zip(regs_ro, data):
        
        rd = yield axi_lite.read_reg(r_addr)
        assert rd == r_value, f'{hex(rd)} == {hex(r_value)}'


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
    run(core, 'cores_nmigen.test.test_axi_lite', ports=ports, vcd_file='./test_axi_lite_device.vcd')