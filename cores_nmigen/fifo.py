from nmigen import *
from nmigen.lib.fifo import SyncFIFOBuffered, SyncFIFO, AsyncFIFO
from .interfaces import AxiStream

class AxiStreamFifo(Elaboratable):

    def __init__(self, width, depth, fifo=SyncFIFOBuffered):
        self.input = AxiStream(width, 'sink', name='input')
        self.output = AxiStream(width, 'source', name='output')
        self.depth = depth
        self.fifo = fifo

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


class AxiStreamFifoCDC(Elaboratable):
    def __init__(self, width, depth, r_domain='read', w_domain='write'):
        self.width = width
        self.input = AxiStream(width, 'sink', name='input')
        self.output = AxiStream(width, 'source', name='output')
        self.depth = depth
        self.r_domain = r_domain
        self.w_domain = w_domain

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync_rd = m.d[self.r_domain]
        sync_wr = m.d[self.w_domain]

        fifo_width = self.width + 1

        m.submodules.fifo_core = fifo = AsyncFIFO(width=fifo_width, depth=self.depth, r_domain=self.r_domain, w_domain=self.w_domain)
        comb += fifo.w_en.eq(self.input.accepted())
        comb += fifo.w_data.eq(Cat(self.input.TDATA, self.input.last))
        comb += self.input.ready.eq(fifo.w_rdy)

        comb += self.output.valid.eq(fifo.r_rdy)
        comb += fifo.r_en.eq(self.output.accepted())

        comb += self.output.TDATA.eq(fifo.r_data[:self.width])
        comb += self.output.TLAST.eq(fifo.r_data[-1])

        return m


if __name__ == '__main__':

    fifo = AxiStreamFifo(16, 128)
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
    main(fifo, ports=ports)

    fifo = AxiStreamFifoCDC(16, 128, r_domain='sync_a', w_domain='sync_b')
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
