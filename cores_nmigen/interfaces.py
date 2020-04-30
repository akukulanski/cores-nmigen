from nmigen import *
from math import ceil, log2
from nmigen.hdl.rec import Direction
import cores_nmigen.utils.matrix as mat

class GenericStream(Record):
    DATA_FIELDS = None
    def __init__(self, direction=None, name=None, fields=None, last=True):
        layout = self.get_layout(direction, last)
        Record.__init__(self, layout, name=name, fields=fields)
        self._total_width = sum([d[1] for d in self.DATA_FIELDS])
        self._flat_data = Cat(*[getattr(self, d[0]) for d in self.DATA_FIELDS])

    def get_layout(self, direction, last):
        if last:
            self.DATA_FIELDS += [('last', 1)]

        if direction == 'sink':
            layout = [('valid', 1, Direction.FANIN),
                      ('ready', 1, Direction.FANOUT)]
            layout += [(d[0], d[1], Direction.FANIN) for d in self.DATA_FIELDS]
        elif direction == 'source':
            layout = [('valid', 1, Direction.FANOUT),
                      ('ready', 1, Direction.FANIN)]
            layout += [(d[0], d[1], Direction.FANOUT) for d in self.DATA_FIELDS]
        else:
            raise ValueError(f'direction should be sink or source.')
        return layout

    def eq_from_flat(self, flat_data):
        ops = []
        start_bit = 0
        assert len(flat_data) == self._total_width
        for df in self.DATA_FIELDS:
            data, width = df[0], df[1]
            ops += [getattr(self, data).eq(flat_data[start_bit:start_bit+width])]
            start_bit += width
        return ops

    def accepted(self):
        return (self.valid == 1) & (self.ready == 1)


class DataStream(GenericStream):
    def __init__(self, width, *args, **kargs):
        self.DATA_FIELDS = [('data', width)]
        GenericStream.__init__(self, *args, **kargs)


class ShifterStream(GenericStream):
    def __init__(self, width, *args, **kargs):
        self.DATA_FIELDS = [('data', width), ('shift', ceil(log2(width+1)))]
        GenericStream.__init__(self, *args, **kargs)


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

class MatrixStream(GenericStream):

    def __init__(self, width, shape, *args, **kwargs):
        self.shape = shape
        self.width = width
        self.DATA_FIELDS = []
        for idx in mat.matrix_indexes(shape):
            text_string = self.get_signal_name(idx)
            self.DATA_FIELDS.append((text_string, width))
        GenericStream.__init__(self, *args, **kwargs)

    def get_signal_name(self, indexes):
        return 'data_' + '_'.join([str(i) for i in indexes])

    @property
    def dimensions(self):
        return mat.get_dimensions(self.shape)

    @property
    def n_elements(self):
        return mat.get_n_elements(self.shape)

    @property
    def data_ports(self):
        for idx in mat.matrix_indexes(self.shape):
            yield getattr(self, self.get_signal_name(idx))

    def connect_data_ports(self, other):
        assert isinstance(other, MatrixStream)
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