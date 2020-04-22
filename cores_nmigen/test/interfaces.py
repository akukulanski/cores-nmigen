import cocotb
from cocotb.drivers import BusDriver
from cocotb.triggers import RisingEdge
import random
import cores_nmigen.utils.matrix as mat


class AxiStreamDriver(BusDriver):
    
    _signals =['TVALID', 'TREADY', 'TLAST', 'TDATA']

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.buffer = []

    def accepted(self):
        return self.bus.TVALID.value.integer == 1 and self.bus.TREADY.value.integer == 1

    def write(self, data):
        self.bus.TDATA <= data

    def read(self):
        return self.bus.TDATA.value.integer

    def read_last(self):
        try:
            return self.bus.TLAST.value.integer
        except:
            return 0

    def _get_random_data(self):
        return random.randint(0, 2**len(self.bus.TDATA)-1)

    @cocotb.coroutine
    def monitor(self):
        while True:
            if self.accepted():
                self.buffer.append(self.read())
            yield RisingEdge(self.clk)

    @cocotb.coroutine
    def send(self, data, burps=False):
        data = list(data)
        while len(data):
            if burps:
                valid = random.randint(0, 1)
            else:
                valid = 1
            self.bus.TVALID <= valid
            if valid:
                self.write(data[0])
                self.bus.TLAST <= 1 if (len(data) == 1) else 0
            else:
                self.write(self._get_random_data())
                self.bus.TLAST <= 0
                # self.bus.TLAST <= random.randint(0, 1)
            yield RisingEdge(self.clk)
            if self.accepted():
                data.pop(0)
        self.bus.TVALID <= 0
        self.bus.TLAST <= 0

    @cocotb.coroutine
    def recv(self, n=-1, burps=False):
        rd = []
        while n:
            if burps:
                ready = random.randint(0, 1)
            else:
                ready = 1
            self.bus.TREADY <= ready
            yield RisingEdge(self.clk)
            if self.accepted():
                rd.append(self.read())
                n = n - 1
                if self.read_last():
                    break
        self.bus.TREADY <= 0
        return rd


class ShifterStreamDriver(AxiStreamDriver):

    _signals =['TVALID', 'TREADY', 'TLAST', 'data', 'shift']

    def write(self, data):
        self.bus.data <= data[0]
        self.bus.shift <= data[1]

    def read(self):
        data = self.bus.data.value.integer
        shift = self.bus.shift.value.integer
        return data, shift

    def _get_random_data(self):
        data = random.randint(0, 2**len(self.bus.data)-1)
        shift = random.randint(0, 2**len(self.bus.shift)-1) 
        return data, shift


class AxiLiteDriver(BusDriver):

    _signals =['AWADDR', 'AWVALID', 'AWREADY',
               'WDATA', 'WSTRB', 'WVALID', 'WREADY',
               'BRESP', 'BVALID', 'BREADY',
               'ARADDR', 'ARVALID', 'ARREADY',
               'RDATA', 'RRESP', 'RVALID', 'RREADY',]

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.registers = {}
        self.transactions = []

    def init_zero(self):
        self.bus.AWADDR <= 0
        self.bus.AWVALID <= 0
        self.bus.WDATA <= 0
        self.bus.WSTRB <= 0
        self.bus.WVALID <= 0
        self.bus.BREADY <= 0
        self.bus.ARADDR <= 0
        self.bus.ARVALID <= 0
        self.bus.RREADY <= 0

    def aw_accepted(self):
        return self.bus.AWVALID.value.integer == 1 and self.bus.AWREADY.value.integer == 1

    def w_accepted(self):
        return self.bus.WVALID.value.integer == 1 and self.bus.WREADY.value.integer == 1

    def b_accepted(self):
        return self.bus.BVALID.value.integer == 1 and self.bus.BREADY.value.integer == 1

    def ar_accepted(self):
        return self.bus.ARVALID.value.integer == 1 and self.bus.ARREADY.value.integer == 1
    
    def r_accepted(self):
        return self.bus.RVALID.value.integer == 1 and self.bus.RREADY.value.integer == 1


    @cocotb.coroutine
    def write_reg(self, addr, value):
        self.bus.AWADDR <= addr
        self.bus.AWVALID <= 1
        yield RisingEdge(self.clk)
        while not self.aw_accepted():
            yield RisingEdge(self.clk)
        self.bus.AWVALID <= 0
        self.bus.WDATA <= value
        self.bus.WVALID <= 1
        yield RisingEdge(self.clk)
        while not self.w_accepted():
            yield RisingEdge(self.clk)
        self.bus.WVALID <= 0
        self.bus.BREADY <= 1
        while not self.b_accepted():
            yield RisingEdge(self.clk)
        self.bus.BREADY <= 0
        yield RisingEdge(self.clk)

    @cocotb.coroutine
    def read_reg(self, addr):
        self.bus.ARADDR <= addr
        self.bus.ARVALID <= 1
        yield RisingEdge(self.clk)
        while not self.ar_accepted():
            yield RisingEdge(self.clk)
        self.bus.ARVALID <= 0
        self.bus.RREADY <= 1
        yield RisingEdge(self.clk)
        while not self.r_accepted():
            yield RisingEdge(self.clk)
        self.bus.RREADY <= 0
        rd = self.rdata
        yield RisingEdge(self.clk)
        return rd

    @cocotb.coroutine
    def monitor(self):
        while True:
            if self.aw_accepted():
                addr_w = self.awaddr
            if self.w_accepted():
                data_w = self.wdata
            if self.ar_accepted():
                addr_r = self.araddr
            if self.r_accepted():
                data_r = self.rdata
            if addr_w is not None and data_w is not None:
                self.transactions.append(('wr', addr_w, data_w))
                self.registers[addr_w] = data_w
                addr_w, data_w = None, None
            if addr_r is not None and data_r is not None:
                self.transactions.append(('rd', addr_r, data_r))
                addr_r, data_r = None, None
            yield RisingEdge(self.clk)

    @property
    def awaddr(self):
        return self.bus.AWADDR.value.integer
    
    @property
    def wdata(self):
        return self.bus.WDATA.value.integer

    @property
    def araddr(self):
        return self.bus.ARADDR.value.integer

    @property
    def rdata(self):
        return self.bus.RDATA.value.integer


class AxiStreamMatrixDriver(AxiStreamDriver):

    _signals =['TVALID', 'TREADY', 'TLAST']

    def __init__(self, entity, name, clock, shape):
        self.shape = shape
        for idx in mat.matrix_indexes(self.shape):
            self._signals.append(self.get_element_name(idx))
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.buffer = []

    def get_element_name(self, indexes):
        return 'TDATA_' + '_'.join([str(i) for i in indexes])

    def get_element(self, indexes):
        return getattr(self.bus, self.get_element_name(indexes))
    
    def write(self, data):
        for idx in mat.matrix_indexes(self.shape):
            self.get_element(idx) <= mat.get_matrix_element(data, idx)

    def read(self):
        matrix = mat.create_empty_matrix(self.shape)
        for idx in mat.matrix_indexes(self.shape):
            mat.set_matrix_element(matrix, idx, self.get_element(idx).value.integer)
        return matrix

    def _get_random_data(self):
        matrix = mat.create_empty_matrix(self.shape)
        for idx in mat.matrix_indexes(self.shape):
            mat.set_matrix_element(matrix, idx, random.randint(0, self._max_value))
        return matrix

    @property
    def _max_value(self):
        width = len(self.get_element(self.first_idx))
        return 2**width - 1

    def init_sink(self):
        self.bus.TVALID <= 0
        self.bus.TLAST <= 0
        for idx in mat.matrix_indexes(self.shape):
            self.get_element(idx) <= 0

    def init_source(self):
        self.bus.TREADY <= 0

    @property
    def first_idx(self):
        return tuple([0] * len(self.shape))