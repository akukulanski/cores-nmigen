from nmigen import *
from math import ceil, log2
from nmigen.hdl.rec import Direction

class MetaStream(Record):
    DATA_FIELDS = []
    def __init__(self, width, direction=None, name=None, fields=None):
        self.width = width
        if direction == 'sink':
            layout = [('valid', 1, Direction.FANIN),
                      ('ready', 1, Direction.FANOUT),
                      ('last', 1, Direction.FANIN)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANIN))
        elif direction == 'source':
            layout = [('valid', 1, Direction.FANOUT),
                      ('ready', 1, Direction.FANIN),
                      ('last', 1, Direction.FANOUT)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANOUT))
        else:
            layout = [('valid', 1),
                      ('ready', 1),
                      ('last', 1)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1]))
        Record.__init__(self, layout, name=name, fields=fields)
        
    def accepted(self):
        return (self.valid == 1) & (self.ready == 1)

class AxiStream(Record):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.width = width
        self.DATA_FIELDS = [('TDATA', width)]
        if direction == 'sink':
            layout = [('TDATA', width, Direction.FANIN),
                      ('TVALID', 1, Direction.FANIN),
                      ('TREADY', 1, Direction.FANOUT),
                      ('TLAST', 1, Direction.FANIN)]
        elif direction == 'source':
            layout = [('TDATA', width, Direction.FANOUT),
                      ('TVALID', 1, Direction.FANOUT),
                      ('TREADY', 1, Direction.FANIN),
                      ('TLAST', 1, Direction.FANOUT)]
        Record.__init__(self, layout, name=name, fields=fields)
        self.valid = self.TVALID
        self.ready = self.TREADY
        self.last = self.TLAST

    def accepted(self):
        return (self.TVALID == 1) & (self.TREADY == 1)

class SymbolStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width), ('length', ceil(log2(width+1)))]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class ShifterStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width), ('shift', ceil(log2(width+1)))]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class Stream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width)]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class AxiLite(Record):
    def __init__(self, addr_w, data_w, mode=None, name=None, fields=None):
        # www.gstitt.ece.ufl.edu/courses/fall15/eel4720_5721/labs/refs/AXI4_specification.pdf#page=122
        assert mode in ('slave',) #('slave', 'master')
        assert data_w in (32, 64)
        self.addr_w = addr_w
        self.data_w = data_w
        if mode == 'slave':
            layout = [('awaddr', addr_w, Direction.FANIN),
                      ('awvalid', 1, Direction.FANIN),
                      ('awready', 1, Direction.FANOUT),
                      ('wdata', data_w, Direction.FANIN),
                      ('wstrb', data_w//8, Direction.FANIN),
                      ('wvalid', 1, Direction.FANIN),
                      ('wready', 1, Direction.FANOUT),
                      ('bresp', 2, Direction.FANOUT),
                      ('bvalid', 1, Direction.FANOUT),
                      ('bready', 1, Direction.FANIN),
                      ('araddr', addr_w, Direction.FANIN),
                      ('arvalid', 1, Direction.FANIN),
                      ('arready', 1, Direction.FANOUT),
                      ('rdata', data_w, Direction.FANOUT),
                      ('rresp', 2, Direction.FANOUT),
                      ('rvalid', 1, Direction.FANOUT),
                      ('rready', 1, Direction.FANIN),]
        elif mode == 'master':
            pass
        Record.__init__(self, layout, name=name, fields=fields)

    def aw_accepted(self):
        return (self.awvalid == 1) & (self.awready == 1)

    def w_accepted(self):
        return (self.wvalid == 1) & (self.wready == 1)

    def b_accepted(self):
        return (self.bvalid == 1) & (self.bready == 1)

    def ar_accepted(self):
        return (self.arvalid == 1) & (self.arready == 1)    

    def r_accepted(self):
        return (self.rvalid == 1) & (self.rready == 1)    

class RegistersInterface(Record):
    _dir = {'ro': Direction.FANIN,
            'rw': Direction.FANOUT}

    def __init__(self, addr_w, data_w, registers, mode=None, name=None, fields=None):
        assert data_w in (32, 64)
        self.addr_w = addr_w
        self.data_w = data_w
        self.registers = registers
        layout = [(reg_name, data_w, self._dir[reg_dir]) for reg_name, reg_dir, reg_addr in self.registers]
        Record.__init__(self, layout, name=name, fields=fields)
