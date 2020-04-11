from nmigen_cocotb import run
from cores_nmigen.fifo import AxiStreamFifo
import random

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
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


@cocotb.coroutine
def check_data(dut, burps_in, burps_out):
    size = 1000
    yield init_axi_test(dut)
    input_stream = AxiStreamDriver(dut, 'input_', dut.clk)
    output_stream = AxiStreamDriver(dut, 'output_', dut.clk)
    data = [random.getrandbits(len(input_stream.bus.TDATA)) for _ in range(size)]
    cocotb.fork(input_stream.send(data, burps=burps_in))
    rcv = yield output_stream.recv(burps=burps_out)
    assert data == rcv

tf_check_data = TF(check_data)
tf_check_data.add_option('burps_in', [False, True])
tf_check_data.add_option('burps_out', [False, True])
tf_check_data.generate_tests()

def test_axi_stream():
    fifo = AxiStreamFifo(random.randint(2, 20), random.randint(2, 10))
    ports = [fifo.input[f] for f in fifo.input.fields]   
    ports += [fifo.output[f] for f in fifo.output.fields]
    run(fifo, 'cores_nmigen.test.test_fifo', ports=ports, vcd_file='axi.vcd')
