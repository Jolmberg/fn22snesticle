#!/usr/bin/env python3

import math
import sys

def sine(start, end, ampl):
    for x in range(start, end):
        x = math.sin(2 * math.pi * x / 64)
        yield round(ampl * x) & 0xffff


def main():
    g = sine(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    print('.word ' + ','.join(f'${x:02x}' for x in g))

if __name__ == '__main__':
    main()
