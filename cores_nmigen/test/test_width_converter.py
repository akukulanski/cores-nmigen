from nmigen_cocotb import run
from cores_nmigen.width_converter import WidthConverter
import pytest
import random
from math import ceil

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

def convertion_ratio(dut):
    maximo = max(len(dut.INPUT__TDATA), len(dut.OUTPUT__TDATA))
    minimo = min(len(dut.INPUT__TDATA), len(dut.OUTPUT__TDATA))
    return maximo // minimo

def calculate_expected_result(data, width_in, width_out):
    if width_in > width_out:
        return [x for x in unpack(data, width_in // width_out, width_out)]
    elif width_in < width_out:
        return [x for x in pack(data, width_out // width_in, width_in)]
    else:
        return [x for x in data]


def pack(buffer, elements, element_width):
    """
        pack generator groups the buffer in packets of "elements"
        considering they have "element_width" bit length.

        args:
            elements: how many elements do you want to join
            element_with: which is the width of each element
        example:
            a = [0, 1, 2, 3, 4, 5]
            b = [p for p in pack(a, 3, 8)]
            result: [0x020100, 0x050403]
    """
    adicionales = (elements - (len(buffer) % elements)) % elements
    buff = buffer + [0]*adicionales
    for i in range(0, len(buff), elements):
        b = 0
        for j in range(elements):
            b = (b << element_width) + buff[i+elements-j-1]
        yield b

def unpack(buffer, elements, element_width):
    """
        unpack generator ungroups the buffer items in "elements"
        parts of "element_with" bit length.

        args:
            elements: In how many parts do you want to split an item.
            element_with: bit length of each part.
        example:
            a = [0x020100, 0x050403]
            b = [p for p in unpack(a, 3, 8)]
            result: [0, 1, 2, 3, 4, 5,]]
    """
    mask = (1 << element_width) - 1
    for b in buffer:
        for _ in range(elements):
            yield (b & mask)
            b = b >> element_width

@cocotb.coroutine
def init_test(dut):
    dut.OUTPUT__TREADY <= 0
    dut.INPUT__TVALID <= 0
    dut.INPUT__TDATA <= 0
    dut.INPUT__TLAST <= 0
    dut.rst <= 1
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)

@cocotb.coroutine
def check_data(dut, multiple, burps):
    """
    description
        Tests the burst capabilities of the width converter.
        If width_in > width_out, during a burst the output_tvalid should remain in 1.
        If width_in < width_out, during a burst the input_tready should remain in 1.

    parameters
        dut         device under test
        multiple    decides whether writing a multiple of the widths ratio or not.
                    In the condition of a TLAST received when there are not enough input packets
                    to complete an output packet, the behaviour of the core is to make it available
                    in the output filling the empty space with zeros and asserting OUTPUT_TLAST.
    """
    axi_driver = AxiStreamDriver if not burps else AxiStreamDriverBurps

    yield init_test(dut)
    input_stream = axi_driver(dut, 'INPUT_', dut.clk)
    output_stream = axi_driver(dut, 'OUTPUT_', dut.clk)
    width_in = len(dut.INPUT__TDATA)
    width_out = len(dut.OUTPUT__TDATA)
    ratio = convertion_ratio(dut)
    
    input_len = 100 * ratio + int(not(multiple))
    output_len = ceil(input_len / ratio)
    data = [random.randint(0, 2**width_in-1) for _ in range(input_len)]

    cocotb.fork(input_stream.send(data))
    rcv = yield output_stream.recv()
    yield RisingEdge(dut.clk)

    expected = calculate_expected_result(data, width_in, width_out)
    assert len(rcv) >= output_len, f'Read {len(rcv)} instead of {output_len} values in burst'
    assert rcv == expected, f'rcv=\n{rcv}\n\nexpected=\n{expected}\n'

tf_test_burst = TF(check_data)
tf_test_burst.add_option('multiple', [True, False])
tf_test_burst.add_option('burps', [True, False])
tf_test_burst.generate_tests()

@pytest.mark.parametrize("width_in, width_out", [(8, 24), (24, 24), (24, 8)])
def test_width_converter(width_in, width_out):
    core = WidthConverter(width_in=width_in,
                          width_out=width_out)
    ports = [core.input[f] for f in core.input.fields]
    ports += [core.output[f] for f in core.output.fields]
    run(core, 'cores_nmigen.test.test_width_converter', ports=ports, vcd_file=f'./output_i{width_in}_o{width_out}.vcd')