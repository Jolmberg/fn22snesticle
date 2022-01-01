#!/usr/bin/env python3

# ISO structure:
# 0x000000 boot.bin (0x440)
# 0x000440 bi2.bin (0x2000)
# 0x002440 apploader.bin (0x1dbb8)
# 0x01fff8 0 (8)
# 0x020000 main.dol (0x4ffa00)
# 0x51fa00 fst.bin
# 0x51fa80 0 (0x5C0)
# 0x520000 opening.bnr (0x1960)
# 0x521960 0 (0x66a0)
# 0x528000 rom (0x200000)

# Source offsets:
# boot.bin       0x00000000
# bi2.bin        0x00000440
# apploader.bin  0x00002440
# main.dol       0x00020000
# banner         0x4873b6cc
# superpunchout  0x56e58000

import argparse
import font
import system_m8
import io
import os
import os.path
import pathlib
import sys
import a2bnr

fst = [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00,
       0x00, 0x52, 0x00, 0x00, 0x00, 0x00, 0x19, 0x60, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x52, 0x80, 0x00,
       0x00, 0x00, 0x00, 0x00, 0x6f, 0x70, 0x65, 0x6e, 0x69, 0x6e, 0x67, 0x2e, 0x62, 0x6e, 0x72, 0x00,
       0x73, 0x6e, 0x73, 0x34, 0x71, 0x30, 0x2e, 0x34, 0x37, 0x31, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

patches = {0xdec74: [0x60000000],
           0xded30: [0x60000000],
           0xdedd4: [0x60000000],
           0xdee44: [0x39200000],
           0xdee9c: [0x60000000],
           0xe9adc: [0x480b3778],
           0x28b560: [0x70091000],  # andi. r9, r0, 0x1000
           0x28b570: [0x61290200],  # ori r9, r9, 0x200
           0x28b5a4: [0x60000000, 0x716a0010],
           0x28b5b0: [0x61292000],
           0x28b5bc: [0x61294000],
           0x28b5c8: [0x61298000],
           0x28b5ec: [0x61290080],
           0x28b5f4: [0x61290040],
           0x28b618: [0x60000000]}

idchars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def hline(banner, x, y, w, colour):
    start = y * 96 + x
    for a in range(start, start + w):
        banner[a] = colour


def vline(banner, x, y, h, colour):
    start = y * 96 + x
    for a in range(start, start + h * 96, 96):
        banner[a] = colour


def rect(banner, x, y, w, h, colour):
    for b in range(y, y + h):
        hline(banner, x, b, w, colour)


def draw_text(banner, x, y, string, fgcolour, shadowcolour=None):
    for (a, b) in font.pixels(system_m8.system_m8, string, basex=x, basey=y):
        pos = 96 * b + a
        if shadowcolour:
            banner[pos + 97] = shadowcolour
        banner[pos] = fgcolour


def draw_text_box(banner, x, y, w, h, string, fgcolour, shadowcolour=None):
    for (a, b) in font.pixels_box(system_m8.system_m8, string, x, y, w, h):
        pos = 96 * b + a
        if shadowcolour:
            banner[pos + 97] = shadowcolour
        banner[pos] = fgcolour


def draw_banner(text, background=(11, 30, 163, 255)):
    bordercolour = (118, 135, 246, 255)
    barcolour = (23, 51, 246, 255)
    lightgrey = (140, 140, 140, 255)
    grey = (112, 112, 112, 255)
    darkgrey = (84, 84, 84, 255)
    brightwhite = (252, 252, 252, 255)
    darkwhite = (192, 192, 192, 255)
    black = (0, 0, 0, 255)
    banner = [background] * 96 * 32
    hline(banner, 0, 0, 96, bordercolour)
    hline(banner, 0, 31, 96, bordercolour)
    vline(banner, 0, 1, 30, bordercolour)
    vline(banner, 95, 1, 30, bordercolour)
    rect(banner, 1, 1, 94, 11, barcolour)  # (height 12 in NESticle)
    rect(banner, 86, 3, 6, 6, grey)
    hline(banner, 86, 2, 7, lightgrey)
    vline(banner, 92, 3, 6, lightgrey)
    vline(banner, 85, 2, 7, darkgrey)
    hline(banner, 85, 9, 7, darkgrey)
    hline(banner, 92, 9, 1, grey)
    draw_text(banner, 6, 2, "SNESticle", brightwhite, black)
    draw_text_box(banner, 6, 13, 88, 19, text, darkwhite, black)
    return banner


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--game-id',
                   help='game id (6 chars, default is to autogenerate)')
    a.add_argument('--game-name',
                   help='short game name string (32 chars, default is ROM)')
    a.add_argument('--long-game-name',
                   help=('long game name string (64 chars, default is "GAME_NAME (SNESticle)")'))
    a.add_argument('--developer', default='',
                   help='short developer string (32 chars, default is empty string)')
    a.add_argument('--long-developer',
                   help='long developer string (64 chars, default is DEVELOPER)')
    a.add_argument('--description',
                   help='game description (128 chars, default is LONG_GAME_NAME)')
    a.add_argument('--header-game-name',
                   help='game name in dvd header (992 chars, default is GAME_NAME)')
    a.add_argument('--banner',
                   help='custom banner image filename')
    a.add_argument('--rom',
                   help='snes rom to include (default is Super Punch-Out!!)')
    a.add_argument('source', metavar='SOURCE',
                   help='source Fight Night 2 iso')
    a.add_argument('target', metavar='TARGET',
                   help='name of the iso file to build')
    args = a.parse_args()

    if args.game_id:
        game_id = args.game_id
    else:
        home = pathlib.Path.home()
        conffile = os.path.join(home, '.fn22snesticle')
        if not os.path.isfile(conffile):
            chars = idchars[0] * 2
            game_id = f'Z{chars}E69'
        else:
            with open(conffile, 'r') as f:
                chars = f.read().strip()
                if chars == idchars[-1] * len(chars):
                    chars = idchars[0] * len(chars)
                    game_id = f'Z{chars}E69'
                    print(f'Warning: Game id wrapped around to {game_id}.', file=sys.stderr)
                else:
                    numbers = [idchars.index(x) for x in chars]
                    numbers[-1] += 1
                    for x in reversed(range(len(numbers))):
                        if numbers[x] >= len(idchars):
                            numbers[x] = 0
                            numbers[x - 1] += 1
                    chars = ''.join(idchars[x] for x in numbers)
                    game_id = f'Z{chars}E69'
        print(f'Generated game id is {game_id}.')

    with open(args.source, 'rb') as source:
        with open(args.target, 'wb') as target:
            # Write boot.bin, bi2.bin and apploader.bin
            target.write(source.read(0x440 + 0x2000 + 0x1dbb8))
            target.write(b'\0' * 8)

            # Write main.dol
            source.seek(0x20000)
            mainstream = io.BytesIO()
            mainstream.write(source.read(0x4ffa00))
            for (k, v) in patches.items():
                mainstream.seek(k)
                for w in v:
                    mainstream.write(w.to_bytes(4, 'big'))
            target.write(mainstream.getvalue())

            # Read rom
            if args.rom:
                if os.path.getsize(args.rom) > 0x1000000:
                    print('Warning: This rom is unreasonably large, it will be truncated.', file=sys.stderr)
                with open(args.rom, 'rb') as rom:
                    romdata = rom.read(0x1000000)
            else:
                source.seek(0x56e58000)
                romdata = source.read(0x200000)
            romlen = len(romdata)

            # Write file system metadata
            fst[0x20] = romlen >> 24
            fst[0x21] = (romlen >> 16) & 255
            fst[0x22] = (romlen >> 8) & 255
            fst[0x23] = romlen & 255
            for x in fst:
                target.write(x.to_bytes(1, 'big'))
            target.write(b'\0' * 0x5C0)

            romname = os.path.basename(args.rom) if args.rom else 'Super Punch-Out!!'
            game_name = args.game_name or romname
            long_game_name = args.long_game_name or f'{game_name} (SNESticle)'
            description = args.description or long_game_name
            long_developer = args.long_developer or args.developer

            # Write banner
            with io.BytesIO() as bannerstream:
                if args.banner:
                    kwargs = {'imagefile': args.banner}
                else:
                    kwargs = {'rgbalist': draw_banner(game_name)}
                if not a2bnr.a2bnr(bannerstream,
                                   name=game_name,
                                   developer=args.developer,
                                   longname=long_game_name,
                                   longdeveloper=long_developer,
                                   description=description,
                                   **kwargs):
                    if args.banner:
                        print(f'Error: Could not convert {args.banner} to a banner file.', file=sys.stderr)
                    else:
                        print('Error: Could not create banner.', file=sys.stderr)
                    sys.exit(1)
                target.write(bannerstream.getvalue())
            target.write(b'\0' * 0x66a0)

            # Write rom
            target.write(romdata)
            target.write(b'\0' * (0x8000 - (romlen & 0x7FFF)))

            # Write game id
            target.seek(0)
            target.write(game_id.encode('latin-1')[:6] + b'\0')

            header_game_name = args.header_game_name or game_name or romname

            # Write game name
            target.seek(0x20)
            hgn = header_game_name.encode('latin-1')
            target.write(hgn + b'\0' * (0x3e0 - len(hgn)))

            # Write fst size to header
            target.seek(0x428)
            data = 0x3b
            target.write(data.to_bytes(4, 'big') * 2)

            # Update config file
            if not args.game_id:
                with open(conffile, 'w') as f:
                    f.write(chars)


if __name__ == '__main__':
    main()
