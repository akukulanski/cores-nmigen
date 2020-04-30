#!/bin/bash

set -xu
yosys -p "read_verilog $1; synth_xilinx -top iz -edif $2" > $2.log
grep -Pzo "=== design hierarchy ===(.|\n)*Estimated number of LCs.*\n" $2.log

