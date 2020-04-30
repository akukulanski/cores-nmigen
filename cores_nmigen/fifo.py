from nmigen import *
from nmigen.lib.fifo import SyncFIFOBuffered, SyncFIFO, AsyncFIFO


class StreamFifo(Elaboratable):

    def __init__(self, input_stream, output_stream, depth, fifo=SyncFIFOBuffered, domain='sync'):
        self.input = input_stream
        self.output = output_stream
        assert self.input._total_width == self.output._total_width
        self.width = self.input._total_width
        self.depth = depth
        self.fifo = fifo
        self.domain = domain

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync = m.d[self.domain]

        m.submodules.fifo_core = fifo = self.fifo(width=self.width, depth=self.depth)

        comb += fifo.w_data.eq(self.input._flat_data)
        comb += fifo.w_en.eq(self.input.accepted())
        comb += self.input.ready.eq(fifo.w_rdy)

        comb += self.output.valid.eq(fifo.r_rdy)
        comb += fifo.r_en.eq(self.output.accepted())
        comb += self.output.eq_from_flat(fifo.r_data)

        return m


if __name__ == '__main__':

    fifo = StreamFifo(input_stream=DataStream(width, 'sink', name='input'),
                      output_stream=DataStream(width, 'source', name='output'),
                      depth=128)
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
    main(fifo, ports=ports)

    # fifo_cdc = StreamFifoCDC(input_stream=DataStream(width, 'sink', name='input'),
    #                          output_stream=DataStream(width, 'source', name='output'),
    #                          depth=128,
    #                          r_domain='sync_a',
    #                          w_domain='sync_b')
    # ports = [fifo_cdc.input[f] for f in fifo_cdc.input.fields]
    # ports += [fifo_cdc.output[f] for f in fifo_cdc.output.fields]
    # main(fifo_cdc, ports=ports)