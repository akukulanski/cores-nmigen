from nmigen import *
from nmigen_cocotb import main
from .interfaces import ShifterStream
from math import ceil, log2

def fixed_shift(data, shift):
    return Cat(data[-shift::], data[0:-shift:])

class StagePipelinedBarrelShifter(Elaboratable):
    def __init__(self, width, shift):
        self.width = width
        self.shift = shift
        self.input = ShifterStream(width, 'sink')
        self.output = ShifterStream(width, 'source')
    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        with m.If(self.input.accepted()):
            sync += self.output.valid.eq(1)
            with m.If(self.input.shift & self.shift):
                sync += self.output.data.eq(fixed_shift(self.input.data, self.shift))
            with m.Else():
                sync += self.output.data.eq(self.input.data)
            sync += self.output.shift.eq(self.input.shift)
            sync += self.output.last.eq(self.input.last)
        with m.Elif(self.output.accepted()):
            sync += self.output.data.eq(0)
            sync += self.output.shift.eq(0)
            sync += self.output.valid.eq(0)
            sync += self.output.last.eq(0)
        with m.If((self.output.valid == 0) | self.output.accepted()):
            comb += self.input.ready.eq(1)
        with m.Else():
            comb += self.input.ready.eq(0)
        return m

        
class PipelinedBarrelShifter(Elaboratable):
    def __init__(self, width):
        self.width = width
        self.input = ShifterStream(width, 'sink', name='input')
        self.output = ShifterStream(width, 'source', name='output')
        self.stages = ceil(log2(self.width))

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        modules = [StagePipelinedBarrelShifter(self.width, 2**i)
                   for i in range(self.stages)]
        for i, stage in enumerate(modules):
            m.submodules['stage_' + str(i)] = stage
        for i in range(1,len(modules)):
            comb += modules[i].input.connect(modules[i-1].output)
        comb += modules[0].input.connect(self.input)
        comb += modules[-1].output.connect(self.output)
        return m

if __name__ == '__main__':
    bs = PipelinedBarrelShifter(48)
    ports = [bs.input[f] for f in bs.input.fields]
    ports += [bs.output[f] for f in bs.output.fields]
    main(bs, ports=ports)
