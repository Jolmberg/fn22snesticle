#!/usr/bin/env python3

import math
import sys


def wave(minampl, maxampl, length):
    rest = 255 - length
    beginning = int(rest /2)
    end = rest - beginning
    mid = (minampl + maxampl) / 2
    ampl = maxampl - mid
    for x in range(beginning):
        yield minampl
    for x in range(length):
        yield round(mid + ampl * math.sin((x-length/2)*math.pi/length))
    for x in range(end):
        yield maxampl

def main():
    minampl = int(sys.argv[1])
    maxampl = int(sys.argv[2])
    length = int(sys.argv[3])
    print('.byte ' + ','.join(f'${x:02x}' for x in wave(minampl, maxampl, length)))

if __name__ == '__main__':
    main()
