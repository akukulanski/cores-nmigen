from nmigen import *
from .interfaces import AxiLite, RegistersInterface


class AxiLiteDevice(Elaboratable):
    def __init__(self, addr_w, data_w, registers):
        self.addr_w = addr_w
        self.data_w = data_w
        self._regs = registers
        self.axi_lite = AxiLite(self.addr_w, self.data_w, 'slave', name='s_axi')
        self.registers = RegistersInterface(addr_w, data_w, registers)

    def write_reg(self, addr, value, m):
        for r in self._regs:
            reg_name, reg_dir, reg_addr = r
            if reg_dir == 'rw':
                with m.If(addr == reg_addr):
                    return getattr(self.registers, reg_name).eq(value)

    def elaborate(self, platform):
        m = Module()
        sync = m.d.sync
        comb = m.d.comb

        # Axi Lite Slave Interface

        wr_addr = Signal(self.addr_w)
        wr_data = Signal(self.data_w)
        
        comb += self.axi_lite.bresp.eq(0)
        comb += self.axi_lite.rresp.eq(0)
        
        with m.FSM() as fsm_rd:
            with m.State("IDLE"):
                comb += self.axi_lite.arready.eq(1)
                comb += self.axi_lite.rvalid.eq(0)
                with m.If(self.axi_lite.ar_accepted()):
                    #########################################################
                    # HOW CAN I COLLAPSE THIS INTO A FUNCION?
                    #sync += ...
                    for r in self._regs:
                        reg_name, reg_dir, reg_addr = r
                        with m.If(self.axi_lite.araddr == reg_addr):
                            sync += self.axi_lite.rdata.eq(getattr(self.registers, reg_name))
                    #########################################################
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
                         self.axi_lite.bvalid.eq(0),]
                with m.If(self.axi_lite.aw_accepted() & self.axi_lite.w_accepted()):
                    #########################################################
                    # HOW CAN I COLLAPSE THIS INTO A FUNCION?
                    #sync += self.write_reg(self.axi_lite.awaddr, self.axi_lite.wdata, m)
                    for r in self._regs:
                        reg_name, reg_dir, reg_addr = r
                        if reg_dir == 'rw':
                            with m.If(self.axi_lite.awaddr == reg_addr):
                                sync += getattr(self.registers, reg_name).eq(self.axi_lite.wdata)
                    #########################################################
                    m.next = "DONE"
                with m.Elif(self.axi_lite.aw_accepted()):
                    sync += wr_addr.eq(self.axi_lite.awaddr)
                    m.next = "WAITING_DATA"
                with m.Elif(self.axi_lite.w_accepted()):
                    sync += wr_data.eq(self.axi_lite.wdata)
                    m.next = "WAITING_ADDR"
            with m.State("WAITING_DATA"):
                comb += [self.axi_lite.awready.eq(0),
                         self.axi_lite.wready.eq(1),
                         self.axi_lite.bvalid.eq(0),]
                with m.If(self.axi_lite.w_accepted()):
                    #########################################################
                    # HOW CAN I COLLAPSE THIS INTO A FUNCION?
                    #sync += self.write_reg(wr_addr, self.axi_lite.wdata, m)
                    for r in self._regs:
                        reg_name, reg_dir, reg_addr = r
                        if reg_dir == 'rw':
                            with m.If(wr_addr == reg_addr):
                                sync += getattr(self.registers, reg_name).eq(self.axi_lite.wdata)
                    #########################################################
                    m.next = "DONE"
            with m.State("WAITING_ADDR"):
                comb += [self.axi_lite.awready.eq(1),
                         self.axi_lite.wready.eq(0),
                         self.axi_lite.bvalid.eq(0),]
                with m.If(self.axi_lite.aw_accepted()):
                    #########################################################
                    # HOW CAN I COLLAPSE THIS INTO A FUNCION?
                    #sync += self.write_reg(self.axi_lite.awaddr, wr_data, m)
                    for r in self._regs:
                        reg_name, reg_dir, reg_addr = r
                        if reg_dir == 'rw':
                            with m.If(self.axi_lite.awaddr == reg_addr):
                                sync += getattr(self.registers, reg_name).eq(wr_data)
                    #########################################################
                    m.next = "DONE"
            with m.State("DONE"):
                comb += [self.axi_lite.awready.eq(0),
                         self.axi_lite.wready.eq(0),
                         self.axi_lite.bvalid.eq(1),]
                with m.If(self.axi_lite.b_accepted()):
                    m.next = "IDLE"

        return m

