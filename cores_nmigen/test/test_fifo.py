from nmigen_cocotb import run
from cores_nmigen.fifo import StreamFifo
from cores_nmigen.interfaces import DataStream
from cores_nmigen.test.interfaces import DataStreamDriver
import random
import pytest

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
except:
    pass


@cocotb.coroutine
def init_axi_test(dut):
    dut.output__ready <= 0
    dut.input__valid <= 0
    dut.input__data <= 0
    dut.input__last <= 0
    dut.rst <= 1
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)


@cocotb.coroutine
def check_data(dut, burps_in, burps_out):
    size = 200
    yield init_axi_test(dut)
    input_stream = DataStreamDriver(dut, 'input_', dut.clk)
    output_stream = DataStreamDriver(dut, 'output_', dut.clk)
    data = [random.getrandbits(len(input_stream.bus.data)) for _ in range(size)]
    cocotb.fork(input_stream.send(data, burps=burps_in))
    rcv = yield output_stream.recv(burps=burps_out)
    assert data == rcv

tf_check_data = TF(check_data)
tf_check_data.add_option('burps_in', [False, True])
tf_check_data.add_option('burps_out', [False, True])
tf_check_data.generate_tests()

@pytest.mark.parametrize("width, depth", [(random.randint(2, 20), random.randint(2, 10))])
def test_main(width, depth):
    fifo = StreamFifo(input_stream=DataStream(width, 'sink', name='input'),
                      output_stream=DataStream(width, 'source', name='output'),
                      depth=depth)
    ports = [fifo.input[f] for f in fifo.input.fields]   
    ports += [fifo.output[f] for f in fifo.output.fields]
    run(fifo, 'cores_nmigen.test.test_fifo', ports=ports, vcd_file='test_stream_fifo.vcd')
