from nmigen import *
from .interfaces import Stream

class StagePipelineDelay(Elaboratable):
    def __init__(self, width):
        self.width = width
        self.input = Stream(width, 'sink')
        self.output = Stream(width, 'source')
    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        with m.If(self.input.accepted()):
            sync += self.output.valid.eq(1)
            sync += self.output.data.eq(self.input.data)
            sync += self.output.last.eq(self.input.last)
        with m.Elif(self.output.accepted()):
            sync += self.output.data.eq(0)
            sync += self.output.valid.eq(0)
            sync += self.output.last.eq(0)
        with m.If((self.output.valid == 0) | self.output.accepted()):
            comb += self.input.ready.eq(1)
        with m.Else():
            comb += self.input.ready.eq(0)
        return m

class PipelineDelay(Elaboratable):
    def __init__(self, width, stages):
        self.width = width
        self.input = Stream(width, 'sink', name='input')
        self.output = Stream(width, 'source', name='output')
        self.stages = stages

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        modules = [StagePipelineDelay(self.width)
                   for i in range(self.stages)]
        for i, stage in enumerate(modules):
            m.submodules['stage_' + str(i)] = stage
        for i in range(1,len(modules)):
            comb += modules[i].input.connect(modules[i-1].output)
        comb += modules[0].input.connect(self.input)
        comb += modules[-1].output.connect(self.output)
        return m