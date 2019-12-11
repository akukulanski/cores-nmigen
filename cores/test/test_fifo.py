from nmigen_cocotb import run
from cores.fifo import AxiStreamFifo
from cores.interfaces import AxiStream
import random
import os

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from .interfaces import AxiStreamDriver
except:
    pass


@cocotb.coroutine
def init_axi_test(dut):
    dut.output__TREADY <= 0
    dut.input__TVALID <= 0
    dut.input__TDATA <= 0
    dut.input__TLAST <= 0
    dut.rst <= 1
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)


@cocotb.test()
def axi_stream_test(dut):
    size = 1000
    yield init_axi_test(dut)
    input_stream = AxiStreamDriver(dut, 'input_', dut.clk)
    output_stream = AxiStreamDriver(dut, 'output_', dut.clk)
    data = [random.getrandbits(len(input_stream.bus.TDATA)) for _ in range(size)]
    cocotb.fork(input_stream.send(data))
    rcv = yield output_stream.recv()
    assert data == rcv


def test_axi_stream():
    fifo = AxiStreamFifo(AxiStream, random.randint(2, 20), random.randint(2, 10))
    ports = [fifo.input[f] for f in fifo.input.fields]   
    ports += [fifo.output[f] for f in fifo.output.fields]
    os.environ['TESTCASE'] = 'axi_stream_test'
    run(fifo, 'cores.test.test_fifo', ports=ports, vcd_file='axi.vcd')
    del(os.environ['TESTCASE'])
