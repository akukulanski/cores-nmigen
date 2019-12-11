from nmigen import *

class EdgeDetector(Elaboratable):
    def __init__(self, type):
        assert type in ('rising', 'falling', 'both')
        self.type = type
        self.input = Signal()
        self.output = Signal()

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        signal_i = Signal()
        sync += signal_i.eq(self.signal)

        if self.type == 'rising':
            comb += self.output.eq((self.signal_i==0) & (self.signal==1))
        elif self.type == 'falling':
            comb += self.output.eq((self.signal_i==1) & (self.signal==0))
        elif self.type == 'both':
            comb += self.output.eq(((self.signal_i==1) & (self.signal==0)) | ((self.signal_i==0) & (self.signal==1)))
