from nmigen_cocotb import run
import cores_nmigen.utils.matrix as mat
from cores_nmigen.test.interfaces import MatrixStreamDriver
from cores_nmigen.test.matrix_bypass import MatrixInterfaceBypass
import pytest
import os

try:
    import cocotb
    from cocotb.triggers import RisingEdge
    from cocotb.clock import Clock
    from cocotb.regression import TestFactory as TF
except:
    pass

CLK_PERIOD_BASE = 100


@cocotb.coroutine
def init_test(dut):
    dut.rst <= 1
    cocotb.fork(Clock(dut.clk, 10, 'ns').start())
    yield RisingEdge(dut.clk)
    dut.rst <= 0
    yield RisingEdge(dut.clk)

def incremental_matrix(shape, size):
    data = []
    count = 0
    for i in range(size):
        matrix = mat.create_empty_matrix(shape)
        for idx in mat.matrix_indexes(shape):
            mat.set_matrix_element(matrix, idx, count)
            count += 1
        data.append(matrix)
    return data


@cocotb.coroutine
def check_data(dut, shape, dummy=0):
    
    test_size = 20
    yield init_test(dut)

    m_axis = MatrixStreamDriver(dut, name='input_', clock=dut.clk, shape=shape)
    s_axis = MatrixStreamDriver(dut, name='output_', clock=dut.clk, shape=shape)
    m_axis.init_sink()
    s_axis.init_source()

    yield RisingEdge(dut.clk)

    wr_data = incremental_matrix(shape, test_size)
    expected_output_length = len(wr_data)

    cocotb.fork(m_axis.monitor())
    cocotb.fork(s_axis.monitor())
    cocotb.fork(s_axis.recv(expected_output_length, burps=False))

    yield m_axis.send(wr_data, burps=False)

    while len(s_axis.buffer) < len(m_axis.buffer):
        yield RisingEdge(dut.clk)

    dut._log.info(f'Buffer in length: {len(m_axis.buffer)}.')
    dut._log.info(f'Buffer out length: {len(s_axis.buffer)}.')
    
    assert len(s_axis.buffer) == expected_output_length, f'{len(s_axis.buffer)} != {expected_output_length}'
    assert m_axis.buffer == s_axis.buffer, f'{m_axis.buffer} == {s_axis.buffer}'


try:
    string_to_tuple = lambda string: tuple([int(i) for i in string.replace('(', '').replace(')', '').split(',')])
    running_cocotb = True
    shape = string_to_tuple(os.environ['coco_param_shape'])
except KeyError as e:
    running_cocotb = False

if running_cocotb:
    tf_test_data = TF(check_data)
    tf_test_data.add_option('shape', [shape])
    tf_test_data.generate_tests()


@pytest.mark.timeout(10)
@pytest.mark.parametrize("width, shape", [(8, (4,2)),
                                          (8, (4,3,2)),
                                         ])
def test_matrix_interface(width, shape):
    os.environ['coco_param_shape'] = str(shape)
    core = MatrixInterfaceBypass(width=width,
                                 shape=shape
                                )
    ports = core.get_ports()
    printable_shape = '_'.join([str(i) for i in shape])
    vcd_file = f'./test_matrix_interface_i{width}_shape{printable_shape}.vcd'
    run(core, 'cores_nmigen.test.test_matrix_interface', ports=ports, vcd_file=vcd_file)
