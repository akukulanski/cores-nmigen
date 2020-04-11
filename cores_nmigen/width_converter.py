from nmigen import *
from .interfaces import AxiStream
from math import ceil

class WidthConverterDown(Elaboratable):
    def __init__(self, width_in, width_out, domain='sync'):
        assert width_in % width_out == 0
        self.width_in = width_in
        self.width_out = width_out
        self.domain = domain
        self.ratio = int(ceil(self.width_in / self.width_out))
        self.input = AxiStream(self.width_in, 'sink', name='INPUT')
        self.output = AxiStream(self.width_out, 'source', name='OUTPUT')

    def elaborate(self, platform):
        m = Module()
        sync = m.d[self.domain]
        comb = m.d.comb
        
        data_buffer = Signal(self.width_in)
        last_buffer = Signal()
        available_data = Signal(range(self.ratio+1))
        buffer_empty = Signal()

        with m.If(available_data == 0):
            comb += buffer_empty.eq(1)
        with m.Else():
            comb += buffer_empty.eq(0)

        with m.If(available_data == 1):
            comb += self.input.TREADY.eq(self.output.accepted())
        with m.Else():
            comb += self.input.TREADY.eq(buffer_empty)

        with m.If(self.input.accepted()):
            sync += data_buffer.eq(self.input.TDATA)
            sync += last_buffer.eq(self.input.TLAST)
            sync += available_data.eq(self.ratio)
        with m.Elif(self.output.accepted()):
            sync += data_buffer.eq(data_buffer >> self.width_out)
            sync += available_data.eq(available_data-1)

        with m.If(available_data == 1):
            comb += self.output.TLAST.eq(last_buffer)
        with m.Else():
            comb += self.output.TLAST.eq(0)

        comb += self.output.TVALID.eq(~buffer_empty)
        comb += self.output.TDATA.eq(data_buffer[0:self.width_out])

        return m

class WidthConverterUp(Elaboratable):
    def __init__(self, width_in, width_out, domain='sync'):
        assert width_out % width_in == 0
        self.width_in = width_in
        self.width_out = width_out
        self.domain = domain
        self.ratio = self.width_out // self.width_in
        self.input = AxiStream(self.width_in, 'sink', name='INPUT')
        self.output = AxiStream(self.width_out, 'source', name='OUTPUT')

    def elaborate(self, platform):
        m = Module()
        sync = m.d[self.domain]
        comb = m.d.comb
        
        data_counter = Signal(range(0, self.ratio+1))
        data_buffer = Array([Signal(self.width_in) for _ in range(self.ratio)])

        for i in range(self.ratio):
            comb += self.output.TDATA[i*self.width_in:(i+1)*self.width_in].eq(data_buffer[i])
        
        with m.If(self.output.accepted()):
            sync += self.output.TVALID.eq(0)
            sync += self.output.TLAST.eq(0)
            for i in range(len(data_buffer)):
                sync += data_buffer[i].eq(0)
        with m.If(self.input.accepted()):
            sync += data_buffer[data_counter].eq(self.input.TDATA)
            with m.If(self.input.TLAST):
                sync += self.output.TVALID.eq(1)
                sync += self.output.TLAST.eq(1)
                sync += data_counter.eq(0)
            with m.Elif(data_counter < self.ratio - 1):
                sync += data_counter.eq(data_counter + 1)
                sync += self.output.TLAST.eq(0)
            with m.Else():
                sync += self.output.TVALID.eq(1)
                sync += self.output.TLAST.eq(0)
                sync += data_counter.eq(0)

        comb += self.input.TREADY.eq((~self.output.TVALID) | (self.output.accepted()))

        return m

class WidthConverterUnity(Elaboratable):
    def __init__(self, width_in, width_out, domain='sync'):
        assert width_in == width_out
        self.width_in = width_in
        self.width_out = width_out
        self.domain = domain
        self.input = AxiStream(self.width_in, 'sink', name='INPUT')
        self.output = AxiStream(self.width_out, 'source', name='OUTPUT')
    def elaborate(self, platform):
        m = Module()
        sync = m.d[self.domain]
        comb = m.d.comb
        # Force synchronic implementation
        dummy = Signal()
        sync += dummy.eq(~dummy)
        #comb += self.output.connect(self.input) # does not work
        comb += self.output.TDATA.eq(self.input.TDATA)
        comb += self.output.TVALID.eq(self.input.TVALID)
        comb += self.output.TLAST.eq(self.input.TLAST)
        comb += self.input.TREADY.eq(self.output.TREADY)
        return m


def WidthConverter(width_in, width_out, domain='sync'):
    if width_in > width_out:
        return WidthConverterDown(width_in, width_out, domain)
    elif width_in < width_out:
        return WidthConverterUp(width_in, width_out, domain)
    else:
         return WidthConverterUnity(width_in, width_out, domain)
