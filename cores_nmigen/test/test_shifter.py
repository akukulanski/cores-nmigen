from nmigen_cocotb import run
from cores_nmigen.shifters import PipelinedBarrelShifter
import random
import pytest

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from .interfaces import *
except:
    pass

@cocotb.coroutine
def init_test(dut):
    dut.output__TREADY <= 0
    dut.input__TVALID <= 0
    dut.input__data <= 0
    dut.input__shift <= 0
    dut.input__TLAST <= 0
    dut.rst <= 0
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)

@cocotb.coroutine
def send_data(stream, data):
    for d in data:
        if isinstance(d, tuple) or isinstance(d, list):
            yield stream.write(*d)
        else:
            yield stream.write(d)

@cocotb.test()
def data_check(dut):
    size = 1000
    yield init_test(dut)
    input_stream = ShifterStreamDriver(dut, 'input_', dut.clk)
    output_stream = ShifterStreamDriver(dut, 'output_', dut.clk)
    input_width = len(input_stream.bus.data)

    for _ in range(5):
        data = [(random.getrandbits(input_width),
                 random.randint(0, input_width-1)) for _ in range(size)]
        cocotb.fork(input_stream.send(data))
        rcv = yield output_stream.recv()

        for idata, odata in zip(data, rcv):
            data = idata[0]
            shift = idata[1]
            shifted = data << shift
            expected = shifted % (2**input_width) + (shifted >> input_width)
            assert expected == odata[0]
            assert idata[1] == odata[1]

@pytest.mark.parametrize("width", [12 * (2**n) for n in range(4)])
def test_main(width):
    shifter = PipelinedBarrelShifter(width)
    ports = [shifter.input[f] for f in shifter.input.fields]   
    ports += [shifter.output[f] for f in shifter.output.fields]
    run(shifter, 'cores_nmigen.test.test_shifter', ports=ports, vcd_file=None)
