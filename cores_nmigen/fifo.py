from nmigen import *
from nmigen.lib.fifo import SyncFIFOBuffered, SyncFIFO, AsyncFIFOBuffered, AsyncFIFO


class StreamFifo(Elaboratable):

    def __init__(self, input_stream, output_stream, depth, fifo=SyncFIFOBuffered, *args, **kwargs):
        assert input_stream._total_width == output_stream._total_width
        self.input = input_stream
        self.output = output_stream
        self.fifo = fifo(width=input_stream._total_width, depth=depth, *args, **kwargs)

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb

        m.submodules.fifo_core = fifo = self.fifo

        comb += fifo.w_data.eq(self.input._flat_data)
        comb += fifo.w_en.eq(self.input.accepted())
        comb += self.input.ready.eq(fifo.w_rdy)

        comb += self.output.valid.eq(fifo.r_rdy)
        comb += fifo.r_en.eq(self.output.accepted())
        comb += self.output.eq_from_flat(fifo.r_data)

        return m


class StreamFifoCDC(StreamFifo):

    def __init__(self, input_stream, output_stream, depth, r_domain, w_domain, fifo=AsyncFIFO):
        StreamFifo.__init__(self, input_stream, output_stream, depth, fifo=fifo,
                            r_domain=r_domain, w_domain=w_domain)

