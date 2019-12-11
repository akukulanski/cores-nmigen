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

class PredictorStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width), ('previous', width)]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class PackerShifterStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width), ('mask', width), ('shift', ceil(log2(width+1)))]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class HuffmanStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('symbol', width),
                            ('length', ceil(log2(width+1))), 
                            ('mask', width)]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class AppenderStream(MetaStream):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('symbol_0', width),
                            ('length_0', ceil(log2(width+1))),
                            ('mask_0', width),
                            ('symbol_1', width),
                            ('length_1', ceil(log2(width+1))),
                            ('mask_1', width)]
        MetaStream.__init__(self, width, direction, name=name, fields=fields)

class HSS(Record):
    DATA_FIELDS = []
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = [('data', width)]
        if direction == 'sink':
            layout = [('valid', 1, Direction.FANIN),
                      ('trigger', 1, Direction.FANOUT),
                      ('available', 1, Direction.FANIN),
                      ('img_coming', 1, Direction.FANIN)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANIN))
        elif direction == 'source':
            layout = [('valid', 1, Direction.FANOUT),
                      ('trigger', 1, Direction.FANIN),
                      ('available', 1, Direction.FANOUT),
                      ('img_coming', 1, Direction.FANOUT)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1], Direction.FANOUT))
        else:
            layout = [('valid', 1),
                      ('trigger', 1),
                      ('available', 1),
                      ('img_coming', 1)]
            for d in self.DATA_FIELDS:
                layout.append((d[0], d[1]))
        Record.__init__(self, layout, name=name, fields=fields)

class SnifferStream(Record):
    def __init__(self, width, direction=None, name=None, fields=None):
        self.DATA_FIELDS = []
        if direction == 'sink':
            layout = [('data', width, Direction.FANIN),
                      ('valid', 1, Direction.FANIN),
                      ('receiving', 1, Direction.FANIN)]
        elif direction == 'source':
            layout = [('data', width, Direction.FANOUT),
                      ('valid', 1, Direction.FANOUT),
                      ('receiving', 1, Direction.FANOUT)]
        else:
            layout = [('data', width),
                      ('valid', 1),
                      ('receiving', 1)]
        Record.__init__(self, layout, name=name, fields=fields)
        
class RoiConfig(Record):
    def __init__(self, direction=None, name=None, fields=None):
        if direction == 'sink':
            layout = [('x0', ceil(log2(80)), Direction.FANIN),
                      ('y0', ceil(log2(5120)), Direction.FANIN),
                      ('x1', ceil(log2(80)), Direction.FANIN),
                      ('y1', ceil(log2(5120)), Direction.FANIN),
                       ('row_length', ceil(log2(81)), Direction.FANIN)]
        elif direction == 'source':
            layout = [('x0', ceil(log2(80)), Direction.FANOUT),
                      ('y0', ceil(log2(5120)), Direction.FANOUT),
                      ('x1', ceil(log2(80)), Direction.FANOUT),
                      ('y1', ceil(log2(5120)), Direction.FANOUT),
                      ('row_length', ceil(log2(81)), Direction.FANOUT)]
        else:
            layout = [('x0', ceil(log2(80))),
                      ('y0', ceil(log2(5120))),
                      ('x1', ceil(log2(80))),
                      ('y1', ceil(log2(5120))),
                      ('row_length', ceil(log2(81)))]
        Record.__init__(self, layout, name=name, fields=fields)