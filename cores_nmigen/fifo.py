from nmigen import *
from nmigen.lib.fifo import SyncFIFOBuffered, SyncFIFO, AsyncFIFO
from .interfaces import AxiStream


class AxiStreamFifo(Elaboratable):
    def __init__(self, width, depth, fifo=SyncFIFO):
        """
        fifo: SyncFIFO, SyncFIFOBuffered
        """
        self.width = width
        self.input = AxiStream(width, 'sink', name='input')
        self.output = AxiStream(width, 'source', name='output')
        self.depth = depth
        self.fifo = fifo
    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync = m.d.sync

        fifo_width = self.width + 1

        m.submodules.fifo_core = fifo = self.fifo(width=fifo_width, depth=self.depth)
        comb += fifo.w_en.eq(self.input.accepted())
        comb += fifo.w_data.eq(Cat(self.input.TDATA, self.input.last))
        comb += self.input.ready.eq(fifo.w_rdy)

        comb += self.output.valid.eq(fifo.r_rdy)
        comb += fifo.r_en.eq(self.output.accepted())

        comb += self.output.TDATA.eq(fifo.r_data[:self.width])
        comb += self.output.TLAST.eq(fifo.r_data[-1])

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

class GenericStreamFifo(Elaboratable):
    def __init__(self, input_stream, output_stream, depth, fifo=SyncFIFOBuffered):
        self.input = input_stream
        self.output = output_stream
        self.depth = depth
        self.fifo = fifo

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync = m.d.sync

        fifo_width = sum([d[1] for d in self.input.DATA_FIELDS])

        m.submodules.fifo_core = fifo = AxiStreamFifo(fifo_width, self.depth, self.fifo)

        input_data = Signal(fifo_width)
        output_data = Signal(fifo_width)

        comb += input_data.eq(Cat(*[self.input[d[0]] for d in self.input.DATA_FIELDS]))

        start_bit = 0
        for df in self.output.DATA_FIELDS:
            data, width = df[0], df[1]
            comb += self.output[data].eq(fifo.output.data[start_bit:start_bit+width])
            start_bit += width

        comb += [fifo.input.valid.eq(self.input.valid),
                 fifo.input.last.eq(self.input.last),
                 fifo.input.data.eq(input_data),
                 self.input.ready.eq(fifo.input.ready),
                ]

        comb += [self.output.valid.eq(fifo.output.valid),
                 self.output.last.eq(fifo.output.last),
                 self.output.data.eq(output_data),
                 fifo.output.ready.eq(self.output.ready),
                ]

        return m




if __name__ == '__main__':

    fifo = AxiStreamFifo(16, 128)
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
    main(fifo, ports=ports)

    fifo = AxiStreamFifoCDC(16, 128, r_domain='sync_a', w_domain='sync_b')
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
