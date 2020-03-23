import argparse
import re
from .width_converter import WidthConverter
from nmigen.hdl.ir import Fragment
from nmigen.back import verilog


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, default='core', help='Core name')
    parser.add_argument('--input_w', type=int, default=64, help='input width')
    parser.add_argument('--output_w', type=int, default=64, help='output width')
    parser.add_argument('file', type=str, metavar='FILE', help='output file (verilog)')
    return parser.parse_args()


def main():
    assert False, 'CLI not implemented!'
    args = get_args()

    core = WidthConverter(args.input_w, args.output_w)
    ports = [core.input[f] for f in core.input.fields]
    ports += [core.output[f] for f in core.output.fields]

    fragment = Fragment.get(core, None)
    output = verilog.convert(fragment, name=args.name, ports=ports)

    with open(args.file, 'w') as f:
        output = re.sub('\*\)', '*/',re.sub('\(\*','/*', output))
        output = output.replace('__', '_')
        f.write(output)


if __name__ == '__main__':
    main()
    
