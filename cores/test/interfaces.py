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

class PredictorStreamDriver(StreamDriver):
    _signals =['valid', 'ready', 'last', 'data', 'previous']

    def write(self, *data):
        self.bus.data <= data[0]
        self.bus.previous <= data[1]

    def read(self):
        data = self.bus.data.value.integer
        previous = self.bus.previous.value.integer
        return data, previous

            
class HuffmanStreamDriver(StreamDriver):
    _signals =['valid', 'ready', 'last', 'symbol', 'mask', 'length']

    def write(self, *data):
        self.bus.symbol <= data[0]
        self.bus.mask <= data[1]
        self.bus.length <= data[2]

    def read(self):
        symbol = self.bus.symbol.value.integer
        length = self.bus.length.value.integer
        mask = self.bus.mask.value.integer
        return symbol, mask, length

class AppenderStreamDriver(StreamDriver):
    _signals =['valid', 'ready', 'last',
               'symbol_0', 'mask_0', 'length_0',
               'symbol_1', 'mask_1', 'length_1']

    def write(self, *data):
        self.bus.symbol_0 <= data[0]
        self.bus.mask_0 <= data[1]
        self.bus.length_0 <= data[2]

        self.bus.symbol_1 <= data[3]
        self.bus.mask_1 <= data[4]
        self.bus.length_1 <= data[5]

    def read(self):
        symbol_0 = self.bus.symbol_0.value.integer
        length_0 = self.bus.length_0.value.integer
        mask_0 = self.bus.mask_0.value.integer
        symbol_1 = self.bus.symbol_1.value.integer
        length_1 = self.bus.length_1.value.integer
        mask_1 = self.bus.mask_1.value.integer
        return symbol_0, mask_0, length_0, symbol_1, mask_1, length_1

        
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

class Pcb3Driver(BusDriver):
    _signals =['available', 'trigger', 'valid', 'img_coming', 'data']

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.buffer = []

    @cocotb.coroutine
    def _send(self, *data):
        self.bus.available <= 1
        while not self.bus.trigger.value.integer:
            yield RisingEdge(self.bus.trigger)
        self.write(*data)
        self.bus.valid <= 1
        yield RisingEdge(self.clk)
        self.bus.valid <= 0

    @cocotb.coroutine
    def _recv(self):
        self.bus.trigger <= 1
        yield RisingEdge(self.clk)
        while (self.bus.valid.value.integer == 0) and (self.bus.img_coming.value.integer == 1):
            yield RisingEdge(self.clk)
        rd = self.read() if self.bus.valid.value.integer == 1 else None
        self.bus.trigger <= 0
        return rd

    @cocotb.coroutine
    def send(self, data):
        self.bus.img_coming <= 1
        for d in data:
            try:
                yield self._send(*d)
            except TypeError:
                yield self._send(d)
        for _ in range(30):
            yield RisingEdge(self.clk)
        self.bus.img_coming <= 0

    @cocotb.coroutine
    def recv(self):
        data = []
        if self.bus.img_coming.value.integer == 0:
            yield RisingEdge(self.bus.img_coming)
        while True:
            d = yield self._recv()
            if d is not None:
                data.append(d)
            else:
                break
        return data

    def write(self, *data):
        self.bus.data <= data[0]

    def read(self):
        rd = self.bus.data.value.integer
        return rd

class Pcb3DriverBurps(Pcb3Driver):
    @cocotb.coroutine
    def _recv(self):
        self.bus.trigger <= random.randint(0, 1)
        yield RisingEdge(self.clk)
        self.bus.trigger <= 0

    @cocotb.coroutine
    def receive_burps(self):
        if self.bus.img_coming.value.integer == 0:
            yield RisingEdge(self.bus.img_coming)
        while self.bus.img_coming.value.integer == 1:
            yield self._recv()

    def accepted(self):
        return self.bus.valid.value.integer == 1

    @cocotb.coroutine
    def monitor(self):
        while True:
            yield RisingEdge(self.clk)
            if self.accepted():
                data = self.read()
                self.buffer.append(data)

class SnifferDriver(BusDriver):
    _signals =['valid', 'receiving', 'data']

    def __init__(self, entity, name, clock):
        BusDriver.__init__(self, entity, name, clock)
        self.clk = clock
        self.buffer = []

    @cocotb.coroutine
    def _send(self, *data):
        self.write(*data)
        self.bus.valid <= 1
        yield RisingEdge(self.clk)
        self.bus.valid <= 0

    @cocotb.coroutine
    def _recv(self):
        yield RisingEdge(self.clk)
        while self.bus.valid.value.integer == 0:
            yield RisingEdge(self.clk)
            if self.bus.receiving.value.integer == 0:
                return None
        return self.read()

    @cocotb.coroutine
    def send(self, data):
        self.bus.receiving <= 1
        for d in data:
            try:
                yield self._send(*d)
            except TypeError:
                yield self._send(d)
        self.bus.receiving <= 0

    @cocotb.coroutine
    def recv(self):
        data = []
        if self.bus.receiving.value.integer == 0:
            yield RisingEdge(self.bus.receiving)
        while True:
            d = yield self._recv()
            if d is None: #self.bus.receiving.value.integer == 0
                return data
            data.append(d)
        return data

    def write(self, *data):
        self.bus.data <= data[0]

    def read(self):
        data = self.bus.data.value.integer
        return data

    @cocotb.coroutine
    def monitor(self):
        while True:
            if self.valid.value.integer:
                data = self.read()
                self.buffer.append(data)
            yield RisingEdge(self.clk)

class SnifferDriverBurps(SnifferDriver):
    @cocotb.coroutine
    def _send(self, *data):
        clocks_to_wait = random.choice(5*[0]+3*[1]+2*[2]+2*[3])
        for _ in range(clocks_to_wait):
            yield RisingEdge(self.clk)
        yield SnifferDriver._send(self, *data)

    @cocotb.coroutine
    def _recv(self):
        clocks_to_wait = random.choice(5*[0]+3*[1]+2*[2]+2*[3])
        for _ in range(clocks_to_wait):
            yield RisingEdge(self.clk)
        data = yield SnifferDriver._recv(self)
        return data