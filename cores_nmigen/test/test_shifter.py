from nmigen_cocotb import run
from cores_nmigen.shifters import PipelinedBarrelShifter
import random
import pytest
from .interfaces import *

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
except:
    pass

@cocotb.coroutine
def init_test(dut):
    dut.output__ready <= 0
    dut.input__valid <= 0
    dut.input__data <= 0
    dut.input__shift <= 0
    dut.input__last <= 0
    dut.rst <= 0
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)


@cocotb.coroutine
def check_data(dut, burps_in, burps_out):
    yield init_test(dut)
    input_stream = ShifterStreamDriver(dut, 'input_', dut.clk)
    output_stream = ShifterStreamDriver(dut, 'output_', dut.clk)
    input_width = len(input_stream.bus.data)
    size = 200

    for _ in range(3):
        data = [(random.getrandbits(input_width),
                 random.randint(0, input_width-1)) for _ in range(size)]
        cocotb.fork(input_stream.send(data, burps=burps_in))
        rcv = yield output_stream.recv(burps=burps_out)

        for idata, odata in zip(data, rcv):
            data = idata[0]
            shift = idata[1]
            shifted = data << shift
            expected = shifted % (2**input_width) + (shifted >> input_width)
            assert expected == odata[0]
            assert idata[1] == odata[1]


tf_test = TF(check_data)
tf_test.add_option('burps_in', [False, True])
tf_test.add_option('burps_out', [False, True])
tf_test.generate_tests()


@pytest.mark.parametrize("width", [12, 24, 48])
def test_main(width):
    shifter = PipelinedBarrelShifter(width)
    ports = [shifter.input[f] for f in shifter.input.fields]   
    ports += [shifter.output[f] for f in shifter.output.fields]
    run(shifter, 'cores_nmigen.test.test_shifter', ports=ports, vcd_file=None)
