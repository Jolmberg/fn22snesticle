#!/usr/bin/env python3

import argparse
import importlib
import os
import sys


def a2bnr(outfile,
          imagefile=None,
          rgbalist=None,
          name=None,
          developer=None,
          longname=None,
          longdeveloper=None,
          description=None,
          patch=False):
    if patch:
        outfile.seek(0x20)
    else:
        outfile.write('BNR1'.encode('latin-1'))
        outfile.write(b'\0' * 0x1C)

    if imagefile or rgbalist:
        if imagefile:
            pi = importlib.import_module('PIL.Image')
            with pi.open(imagefile) as img:
                img2 = img.convert('RGBA')
            pixels = img2.getdata()
        else:
            pixels = rgbalist

        width = 96
        height = 32

        if len(pixels) > width * height:
            print('Warning: Too many pixels in source, result will probably not be great.', file=sys.stderr)
        elif len(pixels) < width * height:
            print('Error: Not enough pixels in source, aborting.', file=sys.stderr)
            return False

        for ty in range(0, height * width, 4 * width):
            for tx in range(0, width, 4):
                for y in range(0, 4 * width, width):
                    for x in range(4):
                        p = pixels[ty + y + tx + x]
                        r = p[0] >> 3
                        g = p[1] >> 3
                        b = p[2] >> 3
                        if len(p) == 4:
                            a = p[3] >> 7
                        else:
                            a = 1
                        outpixels = (a << 15) | (r << 10) | (g << 5) | b
                        outfile.write(outpixels.to_bytes(2, 'big'))
    elif patch:
        outfile.seek(0x1800, 1)
    else:
        return False

    msg(name, 32, outfile, patch)
    msg(developer, 32, outfile, patch)
    msg(longname, 64, outfile, patch)
    msg(longdeveloper, 64, outfile, patch)
    msg(description, 128, outfile, patch)
    return True


def msg(text, chars, outfile, patch):
    if text is not None:
        text = text.encode('latin-1')[:chars]
    if patch and (text is None):
        outfile.seek(chars, 1)
    else:
        if text is None:
            text = b''
        outfile.write(text)
        outfile.write(b'\0' * (chars - len(text)))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--game-name',
                   help='short game name string (32 chars)')
    a.add_argument('--long-game-name',
                   help='long game name string (64 chars)')
    a.add_argument('--developer',
                   help='short developer string (32 chars)')
    a.add_argument('--long-developer',
                   help='long developer string (64 chars)')
    a.add_argument('--description',
                   help='game description (128 chars)')
    a.add_argument('--image',
                   help='source image file')
    a.add_argument('bannerfile', metavar='TARGET',
                   help='output filename')
    args = a.parse_args()
    patch = False
    if args.bannerfile == '-':
        outfile = sys.stdout
    else:
        if os.path.isfile(args.bannerfile):
            patch = True
            outfile = open(args.bannerfile, 'rb+')
        else:
            if not args.image:
                print('Error: --image is required when target does not already exist', file=sys.stderr)
                sys.exit(1)
            outfile = open(args.bannerfile, 'wb+')

    a2bnr(outfile, args.image, args.game_name, args.developer, args.long_game_name,
          args.long_developer, args.description, patch=patch)


if __name__ == '__main__':
    main()
