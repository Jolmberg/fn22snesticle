#!/usr/bin/env python3

import sys
import io


def decompress(stream):
    output = io.BytesIO()
    planes = 0
    while planes < 0x30 * 2:
        favourite = stream.read(1)
        control = stream.read(1)[0]
        for x in range(8):
            if control & 0x80:
                output.write(stream.read(1))
            else:
                output.write(favourite)
            control <<= 1
        planes += 1
    return output


def main():
    with open(sys.argv[1], 'rb') as f:
        f.seek(0x56e58000 + 0x38ab2)
        output = decompress(f)

    print('.byte ' + ','.join(f'${x:02x}' for x in output.getvalue()))


if __name__ == '__main__':
    main()
