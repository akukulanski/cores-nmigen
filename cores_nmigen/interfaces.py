from nmigen import *
from math import ceil, log2
from nmigen.hdl.rec import Direction
import cores_nmigen.utils.matrix as mat

class MetaStream(Record):
    DATA_FIELDS = []
    def __init__(self, width, direction=None, name=None, fields=None):
        self.width = width
        if direction == 'sink':
            layout = [('TVALID', 1, Direction.FANIN),
                      ('TREADY', 1, Direction.FANOUT),
                      ('TLAST', 1, Direction.FANIN)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANIN))
        elif direction == 'source':
            layout = [('TVALID', 1, Direction.FANOUT),
                      ('TREADY', 1, Direction.FANIN),
                      ('TLAST', 1, Direction.FANOUT)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANOUT))
        else:
            layout = [('TVALID', 1),
                      ('TREADY', 1),
                      ('TLAST', 1)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1]))
        Record.__init__(self, layout, name=name, fields=fields)
        self.valid = self.TVALID
        self.ready = self.TREADY
        self.last = self.TLAST
        
    def accepted(self):
        return (self.valid == 1) & (self.ready == 1)


class AxiStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('TDATA', width)]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)
        self.data = self.TDATA


class ShifterStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width), ('shift', ceil(log2(width+1)))]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)


class AxiLite(Record):
    def __init__(self, addr_w, data_w, mode=None, name=None, fields=None):
        # www.gstitt.ece.ufl.edu/courses/fall15/eel4720_5721/labs/refs/AXI4_specification.pdf#page=122
        assert mode in ('slave',) #('slave', 'master')
        assert data_w in (32, 64)
        self.addr_w = addr_w
        self.data_w = data_w
        if mode == 'slave':
            layout = [('AWADDR', addr_w, Direction.FANIN),
                      ('AWVALID', 1, Direction.FANIN),
                      ('AWREADY', 1, Direction.FANOUT),
                      ('WDATA', data_w, Direction.FANIN),
                      ('WSTRB', data_w//8, Direction.FANIN),
                      ('WVALID', 1, Direction.FANIN),
                      ('WREADY', 1, Direction.FANOUT),
                      ('BRESP', 2, Direction.FANOUT),
                      ('BVALID', 1, Direction.FANOUT),
                      ('BREADY', 1, Direction.FANIN),
                      ('ARADDR', addr_w, Direction.FANIN),
                      ('ARVALID', 1, Direction.FANIN),
                      ('ARREADY', 1, Direction.FANOUT),
                      ('RDATA', data_w, Direction.FANOUT),
                      ('RRESP', 2, Direction.FANOUT),
                      ('RVALID', 1, Direction.FANOUT),
                      ('RREADY', 1, Direction.FANIN),]
        elif mode == 'master':
            pass
        Record.__init__(self, layout, name=name, fields=fields)
        self.awaddr = self.AWADDR
        self.awvalid = self.AWVALID
        self.awready = self.AWREADY
        self.wdata = self.WDATA
        self.wstrb = self.WSTRB
        self.wvalid = self.WVALID
        self.wready = self.WREADY
        self.bresp = self.BRESP
        self.bvalid = self.BVALID
        self.bready = self.BREADY
        self.araddr = self.ARADDR
        self.arvalid = self.ARVALID
        self.arready = self.ARREADY
        self.rdata = self.RDATA
        self.rresp = self.RRESP
        self.rvalid = self.RVALID
        self.rready = self.RREADY

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
        assert max([reg[2] for reg in registers]) < 2**addr_w, 'Register with address 0x{:x} not reachable. Increase address width!'.format(max([reg[2] for reg in registers]))
        self.addr_w = addr_w
        self.data_w = data_w
        self.registers = registers
        layout = []
        for r_name, r_dir, r_addr, r_fields in self.registers:
            layout += [(f_name, f_size, self._dir[r_dir]) for f_name, f_size, f_offset in r_fields]
        Record.__init__(self, layout, name=name, fields=fields)

class AxiStreamMatrix(MetaStream):

    def __init__(self, width, shape, direction=None, name=None, fields=None):
        self.shape = shape
        self.width = width
        self.DATA_FIELDS = []
        for idx in mat.matrix_indexes(shape):
            text_string = self.get_signal_name(idx)
            self.DATA_FIELDS.append((text_string, width))
        MetaStream.__init__(self, width, direction=direction, name=name, fields=fields)

    def get_signal_name(self, indexes):
        return 'TDATA_' + '_'.join([str(i) for i in indexes])

    @property
    def dimensions(self):
        return mat.get_dimensions(self.shape)

    @property
    def n_elements(self):
        return mat.get_n_elements(self.shape)

    def accepted(self):
        return (self.TVALID == 1) & (self.TREADY == 1)

    @property
    def data_ports(self):
        for idx in mat.matrix_indexes(self.shape):
            yield getattr(self, self.get_signal_name(idx))

    def connect_data_ports(self, other):
        assert isinstance(other, AxiStreamMatrix)
        return [data_o.eq(data_i) for data_o, data_i in zip(self.data_ports, other.data_ports)]

    def connect_to_const(self, const=0):
        return [data_o.eq(const) for data_o in self.data_ports]

    @property
    def matrix(self):
        interface = self
        class MatrixPort():
            def __getitem__(self_mp, tup):
                if not hasattr(tup, '__iter__'):
                    tup = (tup,)
                assert len(tup) == len(interface.shape), f'{len(tup)} == {len(interface.shape)}'
                return getattr(interface, interface.get_signal_name(tup))
        return MatrixPort()

    @property
    def flatten_matrix(self):
        return [self.matrix[idx] for idx in mat.matrix_indexes(self.shape)]