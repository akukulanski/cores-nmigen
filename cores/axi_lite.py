from nmigen import *
from .interfaces import AxiLite, RegistersInterface


class AxiLiteDevice(Elaboratable):
    def __init__(self, addr_w, data_w, registers):
        self.addr_w = addr_w
        self.data_w = data_w
        self._regs = registers
        self.axi_lite = AxiLite(self.addr_w, self.data_w, 'slave', name='s_axi')
        self.registers = RegistersInterface(addr_w, data_w, registers)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Registers

        regs = {}
        for _, r_dir, addr, r_fields in self._regs:
            regs[addr] = Signal(self.data_w)
            for name, size, offset in r_fields:
                if r_dir == 'rw':
                    comb += getattr(self.registers, name).eq(regs[addr][offset:offset+size])
                else:
                    comb += regs[addr][offset:offset+size].eq(getattr(self.registers, name))

        we = Signal()
        wr_addr = Signal(self.addr_w)
        wr_data = Signal(self.data_w)

        with m.If(self.axi_lite.aw_accepted()):
            sync += wr_addr.eq(self.axi_lite.awaddr)

        with m.If(self.axi_lite.w_accepted()):
            sync += wr_data.eq(self.axi_lite.wdata)
        
        for _, r_dir, r_addr, r_fields in self._regs:
            if r_dir == 'rw':
                with m.If((wr_addr == r_addr) & (we == 1)):
                    sync += regs[r_addr].eq(wr_data)

        for _, r_dir, r_addr, r_fields in self._regs:
            with m.If(self.axi_lite.ar_accepted() & (self.axi_lite.araddr == r_addr)):
                sync += self.axi_lite.rdata.eq(regs[r_addr])

        # Axi Lite Slave Interface
        
        comb += self.axi_lite.rresp.eq(0)
        comb += self.axi_lite.bresp.eq(0)
        
        with m.FSM() as fsm_rd:
            with m.State("IDLE"):
                comb += self.axi_lite.arready.eq(1)
                comb += self.axi_lite.rvalid.eq(0)
                with m.If(self.axi_lite.ar_accepted()):
                    m.next = "READ"
            with m.State("READ"):
                comb += self.axi_lite.arready.eq(0)
                comb += self.axi_lite.rvalid.eq(1)
                with m.If(self.axi_lite.r_accepted()):
                    sync += self.axi_lite.rdata.eq(0)
                    m.next = "IDLE"

        with m.FSM() as fsm_wr:
            with m.State("IDLE"):
                comb += [self.axi_lite.awready.eq(1),
                         self.axi_lite.wready.eq(1),
                         self.axi_lite.bvalid.eq(0),
                         we.eq(0),]
                with m.If(self.axi_lite.aw_accepted() & self.axi_lite.w_accepted()):
                    m.next = "DONE"
                with m.Elif(self.axi_lite.aw_accepted()):
                    m.next = "WAITING_DATA"
                with m.Elif(self.axi_lite.w_accepted()):
                    m.next = "WAITING_ADDR"
            with m.State("WAITING_DATA"):
                comb += [self.axi_lite.awready.eq(0),
                         self.axi_lite.wready.eq(1),
                         self.axi_lite.bvalid.eq(0),
                         we.eq(0),]
                with m.If(self.axi_lite.w_accepted()):
                    m.next = "DONE"
            with m.State("WAITING_ADDR"):
                comb += [self.axi_lite.awready.eq(1),
                         self.axi_lite.wready.eq(0),
                         self.axi_lite.bvalid.eq(0),
                         we.eq(0),]
                with m.If(self.axi_lite.aw_accepted()):
                    m.next = "DONE"
            with m.State("DONE"):
                comb += [self.axi_lite.awready.eq(0),
                         self.axi_lite.wready.eq(0),
                         self.axi_lite.bvalid.eq(1),
                         we.eq(1),]
                with m.If(self.axi_lite.b_accepted()):
                    m.next = "IDLE"

        return m

