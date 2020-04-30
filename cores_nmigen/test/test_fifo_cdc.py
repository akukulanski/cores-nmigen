from nmigen_cocotb import run
from cores_nmigen.fifo import StreamFifoCDC
from cores_nmigen.interfaces import DataStream
from cores_nmigen.test.interfaces import DataStreamDriver
import random
import pytest
import os

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF #renamed different than "Test*" so pytest won't show up a warning
except:
    pass

random.seed()

@cocotb.coroutine
def init_test(dut, period_ns_w, period_ns_r):
    dut.output__ready <= 0
    dut.input__valid <= 0
    dut.input__data <= 0
    dut.input__last <= 0
    dut.write_rst <= 1
    dut.read_rst <= 1
    cocotb.fork(Clock(dut.write_clk, period_ns_w, 'ns').start())
    cocotb.fork(Clock(dut.read_clk, period_ns_r, 'ns').start())
    yield RisingEdge(dut.write_clk)
    yield RisingEdge(dut.write_clk)
    yield RisingEdge(dut.read_clk)
    yield RisingEdge(dut.read_clk)
    dut.write_rst <= 0
    dut.read_rst <= 0
    yield RisingEdge(dut.write_clk)
    yield RisingEdge(dut.read_clk)
    yield RisingEdge(dut.write_clk)
    yield RisingEdge(dut.read_clk)

@cocotb.coroutine
def check_data(dut, period_ns_w, period_ns_r, burps_in, burps_out, dummy=0):
    length = 200
    yield init_test(dut, period_ns_w, period_ns_r)
    input_stream = DataStreamDriver(dut, 'input_', dut.write_clk)
    output_stream = DataStreamDriver(dut, 'output_', dut.read_clk)
    data = [random.getrandbits(len(input_stream.bus.data)) for _ in range(length)]
    cocotb.fork(input_stream.send(data, burps=burps_in))
    rcv = yield output_stream.recv(burps=burps_out)
    assert data == rcv, f'\n{data}\n!=\n{rcv}'


tf_check = TF(check_data)
tf_check.add_option('period_ns_w', [10])
tf_check.add_option('period_ns_r', [10, 22, 3])
tf_check.add_option('burps_in',  [False, True])
tf_check.add_option('burps_out', [False, True])
tf_check.add_option('dummy', [0] * 3)
tf_check.generate_tests(postfix='_cdc')


@pytest.mark.parametrize("width, depth", [(random.randint(2, 20), random.randint(2, 10))])
def test_main(width, depth):
    fifo = StreamFifoCDC(input_stream=DataStream(width, 'sink', name='input'),
                         output_stream=DataStream(width, 'source', name='output'),
                         depth=depth,
                         r_domain='read',
                         w_domain='write')
    ports = [fifo.input[f] for f in fifo.input.fields]   
    ports += [fifo.output[f] for f in fifo.output.fields]
    run(fifo, 'cores_nmigen.test.test_fifo_cdc', ports=ports, vcd_file='test_stream_fifo_cdc.vcd')
