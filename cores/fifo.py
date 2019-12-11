from nmigen import *
from nmigen.lib.fifo import SyncFIFOBuffered, SyncFIFO
from .interfaces import Stream

class AxiStreamFifo(Elaboratable):
    def __init__(self, stream_type, width, depth, force_sync_rd=False):
        self.input = stream_type(width, 'sink', name='input')
        self.output = stream_type(width, 'source', name='output')
        self.depth = depth
        self.fifo = SyncFIFOBuffered if force_sync_rd else SyncFIFO
    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync = m.d.sync

        input_data_signals = [self.input[d[0]] for d in self.input.DATA_FIELDS]
        fifo_width = sum([d[1] for d in self.input.DATA_FIELDS]) + 1

        fifo = m.submodules.fifo_core = self.fifo(width=fifo_width, depth=self.depth)
        comb += fifo.w_en.eq(self.input.accepted())
        comb += fifo.w_data.eq(Cat(*input_data_signals, self.input.last))
        comb += self.input.ready.eq(fifo.w_rdy)

        comb += self.output.valid.eq(fifo.r_rdy)
        comb += fifo.r_en.eq(self.output.accepted())

        start_bit = 0
        for df in self.output.DATA_FIELDS:
            d = df[0]
            w = df[1]
            comb += self.output[d].eq(fifo.r_data[start_bit:start_bit+w])
            start_bit += w
        comb += self.output.last.eq(fifo.r_data[-1])

        return m
