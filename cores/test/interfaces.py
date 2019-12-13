import cocotb
from cocotb.drivers import BusDriver
from cocotb.triggers import RisingEdge
import random

class StreamDriver(BusDriver):
    _signals =['valid', 'ready', 'last', 'data']

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.buffer = []

    def accepted(self):
        return self.bus.valid.value.integer == 1 and self.bus.ready.value.integer == 1

    @cocotb.coroutine
    def _send(self, *data):
        self.write(*data)
        self.bus.valid <= 1
        yield RisingEdge(self.clk)
        while not self.accepted():
            yield RisingEdge(self.clk)
        self.bus.valid <= 0

    @cocotb.coroutine
    def _recv(self):
        self.bus.ready <= 1
        yield RisingEdge(self.clk)
        while not self.accepted():
            yield RisingEdge(self.clk)
        self.bus.ready <= 0
        return self.read()

    @cocotb.coroutine
    def send(self, data):
        for d in data[:-1]:
            try:
                yield self._send(*d)
            except TypeError:
                yield self._send(d)
        self.bus.last <= 1
        try:
            yield self._send(*data[-1])
        except TypeError:
            yield self._send(data[-1])
        self.bus.last <= 0

    @cocotb.coroutine
    def recv(self):
        data = []
        while True:
            d = yield self._recv()
            data.append(d)
            if self.bus.last.value.integer == 1:
                break
        return data

    def write(self, *data):
        self.bus.data <= data[0]

    def read(self):
        data = self.bus.data.value.integer
        return data

    @cocotb.coroutine
    def monitor(self):
        while True:
            if self.accepted():
                data = self.read()
                self.buffer.append(data)
            yield RisingEdge(self.clk)

    
class ShifterStreamDriver(StreamDriver):
    _signals =['valid', 'ready', 'last', 'data', 'shift']

    def write(self, *data):
        self.bus.data <= data[0]
        self.bus.shift <= data[1]

    def read(self):
        data = self.bus.data.value.integer
        shift = self.bus.shift.value.integer
        return data, shift

        
class AxiStreamDriver(StreamDriver):
    _signals =['TVALID', 'TREADY', 'TLAST', 'TDATA']

    def accepted(self):
        return self.bus.TVALID.value.integer == 1 and self.bus.TREADY.value.integer == 1

    @cocotb.coroutine
    def _send(self, *data):
        self.write(*data)
        self.bus.TVALID <= 1
        yield RisingEdge(self.clk)
        while not self.accepted():
            yield RisingEdge(self.clk)
        self.bus.TVALID <= 0

    @cocotb.coroutine
    def _recv(self):
        self.bus.TREADY <= 1
        yield RisingEdge(self.clk)
        while not self.accepted():
            yield RisingEdge(self.clk)
        self.bus.TREADY <= 0
        return self.read()

    @cocotb.coroutine
    def send(self, data):
        for d in data[:-1]:
            try:
                yield self._send(*d)
            except TypeError:
                yield self._send(d)
        self.bus.TLAST <= 1
        try:
            yield self._send(*data[-1])
        except TypeError:
            yield self._send(data[-1])
        self.bus.TLAST <= 0

    @cocotb.coroutine
    def recv(self):
        data = []
        while True:
            d = yield self._recv()
            data.append(d)
            if self.bus.TLAST.value.integer == 1:
                break
        return data

    def write(self, *data):
        self.bus.TDATA <= data[0]

    def read(self):
        data = self.bus.TDATA.value.integer
        return data

class AxiStreamDriverBurps(AxiStreamDriver):
    @cocotb.coroutine
    def _send(self, *data):
        clocks_to_wait = random.choice(5*[0]+3*[1]+2*[2]+2*[3])
        for _ in range(clocks_to_wait):
            yield RisingEdge(self.clk)
        yield AxiStreamDriver._send(self, *data)

    @cocotb.coroutine
    def _recv(self):
        clocks_to_wait = random.choice(5*[0]+3*[1]+2*[2]+2*[3])
        for _ in range(clocks_to_wait):
            yield RisingEdge(self.clk)
        data = yield AxiStreamDriver._recv(self)
        return data


class AxiLiteDriver(BusDriver):
    _signals =['awaddr', 'awvalid', 'awready',
               'wdata', 'wstrb', 'wvalid', 'wready',
               'bresp', 'bvalid', 'bready',
               'araddr', 'arvalid', 'arready',
               'rdata', 'rresp', 'rvalid', 'rready',]

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.registers = {}
        self.transactions = []

    def aw_accepted(self):
        return self.bus.awvalid.value.integer == 1 and self.bus.awready.value.integer == 1

    def w_accepted(self):
        return self.bus.wvalid.value.integer == 1 and self.bus.wready.value.integer == 1

    def b_accepted(self):
        return self.bus.bvalid.value.integer == 1 and self.bus.bready.value.integer == 1

    def ar_accepted(self):
        return self.bus.arvalid.value.integer == 1 and self.bus.arready.value.integer == 1
    
    def r_accepted(self):
        return self.bus.rvalid.value.integer == 1 and self.bus.rready.value.integer == 1


    @cocotb.coroutine
    def write_reg(self, addr, value):
        self.bus.awaddr <= addr
        self.bus.awvalid <= 1
        yield RisingEdge(self.clk)
        while not self.aw_accepted():
            yield RisingEdge(self.clk)
        self.bus.awvalid <= 0
        self.bus.wdata <= value
        self.bus.wvalid <= 1
        yield RisingEdge(self.clk)
        while not self.w_accepted():
            yield RisingEdge(self.clk)
        self.bus.wvalid <= 0
        self.bus.bready <= 1
        while not self.b_accepted():
            yield RisingEdge(self.clk)
        self.bus.bready <= 0
        yield RisingEdge(self.clk)

    @cocotb.coroutine
    def read_reg(self, addr):
        self.bus.araddr <= addr
        self.bus.arvalid <= 1
        yield RisingEdge(self.clk)
        while not self.ar_accepted():
            yield RisingEdge(self.clk)
        self.bus.arvalid <= 0
        self.bus.rready <= 1
        yield RisingEdge(self.clk)
        while not self.r_accepted():
            yield RisingEdge(self.clk)
        self.bus.rready <= 0
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
        return self.bus.awaddr.value.integer
    
    @property
    def wdata(self):
        return self.bus.wdata.value.integer

    @property
    def araddr(self):
        return self.bus.araddr.value.integer

    @property
    def rdata(self):
        return self.bus.rdata.value.integer