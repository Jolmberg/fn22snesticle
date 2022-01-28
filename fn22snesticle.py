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
# font           0x56e90ab2

import argparse
import font
import system_m8
import io
import os
import os.path
import pathlib
import sys
import a2bnr
import spof


p_main = {0xdec74: [0x60000000],   # nop ; Null references
          0xded30: [0x60000000],   # nop
          0xdedd4: [0x60000000],   # nop
          0xdee44: [0x39200000],   # li r9, 0
          0xdee9c: [0x60000000],   # nop
          0xe9adc: [0x480b3778],   # b 0x801a0254 ; Jump to snesticle
          0x28b560: [0x70091000],  # andi. r9, r0, 0x1000 ; Move start check
          0x28b570: [0x61290200],  # ori r9, r9, 0x200
          0x28b5a4: [0x60000000,   # nop ; Remove Select from Y
                     0x716a0010],  # andi. r10, r11, 0x0010 ; Set Select to Z
          0x28b5b0: [0x61292000],  # ori r9, r9, 0x2000
          0x28b618: [0x60000000]}  # nop ; Don't exit on Z

p_buttons = {0x28b5bc: [0x61294000],  # ori r9, r9, 0x4000
             0x28b5c8: [0x61298000],  # ori r9, r9, 0x8000
             0x28b5ec: [0x61290080],  # ori r9, r9, 0x0080
             0x28b5f4: [0x61290040]}  # ori r9, r9, 0x0040

p_multirom = {0x28b618: [0x713f9080],      # andi. r31, r9, 0x9080 ; Exit on A/B/Start
              0x28b4c8: [0x60000000],      # nop ; Null reference on snesticle exit
              0x27cb7c: [0x60000000] * 7,  # nop * 7 ; More
              0x28aef8: [0x60000000],      # nop ; More
              0x19d260: [0x3c608063,       # lis  r3, -0x7f9f
                         0x3863aa8c,       # addi r3, r3, -0x5574
                         0x80630024,       # lwz  r3, 0x24(r3) ; Read game file name
                         0x3c808049,       # lis  r4, -0x7fb7
                         0x388463ac,       # addi r4, r4, 0x63ac
                         0x90640000,       # stw  r3, 0(r4) ; Store game file name
                         0x3c608029,       # lis  r3, -0x7fd7
                         0x3863e618,       # addi r3, r3, -0x19e8
                         0x3c806000,       # lis  r4, 0x6000
                         0x90830000,       # stw  r4, 0(r3) ; Never exit snesticle
                         0x38800100,       # addi r4, 0, 0x0100
                         0x4822d7a5,       # bl ICInvalidateRange
                         0x4bffffcc]}      # b 0x801a025c

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


def draw_logo(text):
    bitmap = []
    for _ in range(8):
        bitmap.append([1] * 128)
    for (x, y) in font.pixels(system_m8.system_m8, text, 16, 0):
        bitmap[y+1][x+1] = 2
        bitmap[y][x] = 3

    tiles = io.BytesIO()
    for ty in range(0, 8, 4):
        for tx in range(0, 128, 4):
            for y in range(8):
                pixels = bitmap[ty + (y >> 1)][tx:tx + 4]
                for p in range(1, 3):
                    v = 0
                    for x in range(8):
                        v += (1 << x) if (pixels[3 - (x >> 1)] & p) else 0
                    tiles.write(v.to_bytes(1, 'big'))
    return tiles


def make_fst(files):
    fst = io.BytesIO()
    entries = len(files)
    filenames = []
    for f in files:
        filenames += list(f[0].encode('ascii')) + [0]
    fstlen = len(filenames) + 12*entries + 12
    if fstlen > 0x600:
        offset = 0x520000 + ((fstlen - 0x600 + 0x7fff) & 0xffff8000)
    else:
        offset = 0x520000
    fst.write(bytes([1, 0, 0, 0, 0, 0, 0, 0]))
    fst.write((entries + 1).to_bytes(4, 'big'))
    foffs = offset
    fnoffs = 0
    for f in files:
        fst.write(fnoffs.to_bytes(4, 'big'))
        fst.write(foffs.to_bytes(4, 'big'))
        fst.write(f[1].to_bytes(4, 'big'))
        fnoffs += len(f[0]) + 1
        foffs += (f[1] + 0x7fff) & 0xffff8000

    fst.write(bytes(filenames))
    if fstlen <= 0x600:
        fst.write(b'\0' * (0x600 - fstlen))
    else:
        fst.write(b'\0' * (0x8000 - (fstlen - 0x600)))
    return (fst, fstlen)


def gamelist(games, keep_extensions):
    stream = io.BytesIO()
    tiles = """0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.',“”:!?-*…# """
    substs = {'"': '”'}
    tmap = {}
    for tile in tiles:
        tmap[tile] = (tiles.index(tile) + 0x40).to_bytes(1, 'big')
    for (l, r) in substs.items():
        tmap[l] = (tiles.index(r) + 0x40).to_bytes(1, 'big')
    for g in games:
        game = g[2]
        if not keep_extensions:
            game = game[:-4]
        game = os.path.basename(game).upper()[:30]
        stream.write(b'\x70\0\x70\0')
        for ch in game:
            stream.write(tmap.get(ch, b'\x70'))
            stream.write(b'\0')
        for x in range(30 - len(game)):
            stream.write(b'\x70\0')

    for x in range((25 - (len(games) % 25)) % 25):
        stream.write(b'\x70\0' * 32)
    return stream


def fnlist(games):
    stream = io.BytesIO()
    for g in games:
        stream.write(g[0].encode('ascii') + b'\0\0')
    return stream


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--game-id',
                   help='game id (6 chars, default is to autogenerate)')
    a.add_argument('--game-name',
                   help='short game name string (32 chars, default is ROM, or "SNESticle" if ROM is a directory)')
    a.add_argument('--long-game-name',
                   help=('long game name string (64 chars, default is "GAME_NAME (SNESticle)", or "SNESticle" if ROM is a directory)'))
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
                   help='snes rom or rom directory to include (default is Super Punch-Out!!)')
    a.add_argument('--literal-buttons', action='store_true',
                   help='use literal button mapping (not recommended)')
    a.add_argument('--no-super-punch-out', action='store_true',
                   help='do not put Super Punch-Out!! on the final iso')
    a.add_argument('--keep-extensions', action='store_true',
                   help='display file extensions in the game selection menu')
    a.add_argument('--dump-menu', metavar='FILE',
                   help='dump menu rom to FILE')
    a.add_argument('source', metavar='SOURCE',
                   help='source Fight Night 2 iso')
    a.add_argument('target', metavar='TARGET',
                   help='name of the iso file to build')
    args = a.parse_args()

    if args.no_super_punch_out and not args.rom:
        print('Error: No Super Punch-Out requested and no rom provided. Try --rom ROM.', file=sys.stderr)
        sys.exit(1)

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

    multirom = args.rom and os.path.isdir(args.rom)

    with open(args.source, 'rb') as source:
        with open(args.target, 'wb') as target:
            # Write boot.bin, bi2.bin and apploader.bin
            target.write(source.read(0x440 + 0x2000 + 0x1dbb8))
            target.write(b'\0' * 8)

            # Write main.dol
            source.seek(0x20000)
            mainstream = io.BytesIO()
            mainstream.write(source.read(0x4ffa00))

            patches = p_main
            if not args.literal_buttons:
                patches.update(p_buttons)
            if multirom:
                patches.update(p_multirom)

            for (k, v) in patches.items():
                mainstream.seek(k)
                for w in v:
                    mainstream.write(w.to_bytes(4, 'big'))
            target.write(mainstream.getvalue())

            if multirom:
                banner_text = args.game_name or 'Thanks Shitman!'
                game_name = args.game_name or 'SNESticle'
                long_game_name = 'SNESticle'
            else:
                romname = os.path.basename(args.rom) if args.rom else 'Super Punch-Out!!'
                game_name = args.game_name or romname
                long_game_name = args.long_game_name or f'{game_name} (SNESticle)'
                banner_text = game_name
            description = args.description or long_game_name
            long_developer = args.long_developer or args.developer

            # Generate banner
            bannerstream = io.BytesIO()
            if args.banner:
                kwargs = {'imagefile': args.banner}
            else:
                kwargs = {'rgbalist': draw_banner(banner_text)}
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

            # Read rom(s)
            files = []
            if args.rom:
                if multirom:
                    ls = os.listdir(args.rom)
                    i = 0
                    for f in ls:
                        if f.lower()[-4:] in ('.sfc', '.smc', '.fig'):
                            realfilename = os.path.join(args.rom, f)
                            size = os.path.getsize(realfilename)
                            fn = (idchars[i // len(idchars)] + idchars[i % len(idchars)]).lower()
                            i += 1
                            files.append((fn, size, realfilename, None))
                    if not files:
                        if args.no_super_punch_out:
                            print('Error: No roms found in the given directory and no Super Punch-Out requested.',
                                  file=sys.stderr)
                            sys.exit(1)
                        else:
                            print('Warning: No roms found in the given directory, enjoy Super Punch-Out!!\n'
                                  'If this is intentional, '
                                  'consider leaving out --rom to produce a Super Punch-Out iso without the game menu.',
                                  file=sys.stderr)
                    if len(files) == 1 and args.no_super_punch_out:
                        print('Warning: Only one rom provided. '
                              'Consider providing its full filename to produce a single-rom iso without the game menu.',
                              file=sys.stderr)
                    if not args.no_super_punch_out:
                        source.seek(0x56e58000)
                        spodata = source.read(0x200000)
                        fn = (idchars[i // len(idchars)] + idchars[i % len(idchars)]).lower()
                        files.append((fn, 0x200000, 'Super Punch-Out!!.sfc', spodata))
                    files.sort(key=lambda x: str.casefold(os.path.basename(x[2])))
                    if len(files) > 506:
                        print('Warning: Too many roms! The first 506 will be included.', file=sys.stderr)
                        files = files[:506]
                else:
                    with open(args.rom, 'rb') as rom:
                        romdata = rom.read()
            else:
                source.seek(0x56e58000)
                romdata = source.read(0x200000)
            if multirom:
                gl = gamelist(files, args.keep_extensions).getvalue()
                fnl = fnlist(files).getvalue()
                menudata = io.BytesIO()

                with open('menu/menu.sfc', 'rb') as f:
                    menudata.write(f.read())
                menudata.seek(0x5000)
                menudata.write(draw_logo("#FreeTheSNESticle").getvalue())
                source.seek(0x56e90ab2)
                menudata.seek(0x5400)
                menudata.write(spof.decompress(source).getvalue())
                menudata.seek(0x6ffe)
                menudata.write((len(files) - 1).to_bytes(2, 'little'))
                menudata.seek(0x7000)
                menudata.write(fnl)
                menudata.seek(0x8000)
                menudata.write(gl)
                files.append(('sns4q0.471', os.path.getsize('menu/menu.sfc'), None, menudata.getvalue()))
                if args.dump_menu:
                    with open(args.dump_menu, 'wb') as f:
                        f.write(menudata.getvalue())
            else:
                romlen = len(romdata)
                files.append(('sns4q0.471', romlen, None, romdata))

            files.insert(-1, ('opening.bnr', 0x1960, None, bannerstream.getvalue()))

            # Write file system metadata
            fst, fstlen = make_fst(files)
            target.write(fst.getvalue())

            # Write files
            for f in files:
                if f[3]:
                    w = target.write(f[3])
                else:
                    with open(f[2], 'rb') as f:
                        w = target.write(f.read())
                target.write(b'\0' * (((w + 0x7fff) & 0xffff8000) - w))

            # Write game id
            target.seek(0)
            target.write(game_id.encode('latin-1')[:6] + b'\0')

            header_game_name = args.header_game_name or game_name

            # Write game name
            target.seek(0x20)
            hgn = header_game_name.encode('latin-1')
            target.write(hgn + b'\0' * (0x3e0 - len(hgn)))

            # Write fst size to header
            target.seek(0x428)
            data = fstlen
            target.write(data.to_bytes(4, 'big') * 2)

            # Update config file
            if not args.game_id:
                print(f'Generated game id is {game_id}.', file=sys.stderr)
                with open(conffile, 'w') as f:
                    f.write(chars)


if __name__ == '__main__':
    main()
