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
          0x28b560: [0x60000000,   # Placeholder for exit check
                     0x54093C2E,   # rlwinm r9, r0, 7, 16, 23
                     0x50094CAC,   # rlwimi 9, 0, 9, 18, 22
                     0x5009452A,   # rlwimi 9, 0, 8, 20, 21
                     0x500904E6,   # rlwimi 9, 0, 0, 19, 19
                     0x5009fEB6,   # rlwimi 9, 0, 31, 26, 27
                     0x50092C62,   # rlwimi 9, 0, 5, 17, 17
                     0x5009EE30,   # rlwimi 9, 0, 29, 24, 24
                     0x5009DE72,   # rlwimi 9, 0, 27, 25, 25

                     0x5529801E,   # rlwinm r9, r9, 16, 0, 15 ; Shift up
                     0x80030094,   # lwz r0, 0x94(r3) ; Load P2

                     0x50093C2E,   # Same as above except rlwimi
                     0x50094CAC,
                     0x5009452A,
                     0x500904E6,
                     0x5009fEB6,
                     0x50092C62,
                     0x5009EE30,
                     0x5009DE72,

                     0x91210008,   # stw r9, 8(r1) ; Store P1, P2
                     0x80030120,   # lwz r0, 0x120(r3) ; Load P3

                     0x54093C2E,
                     0x50094CAC,
                     0x5009452A,
                     0x500904E6,
                     0x5009fEB6,
                     0x50092C62,
                     0x5009EE30,
                     0x5009DE72,

                     0x5529801E,   # rlwinm r9, r9, 16, 0, 15 ; Shift up
                     0x800301ac,   # lwz r0, 0x1ac(r3) ; Load P4

                     0x50093C2E,
                     0x50094CAC,
                     0x5009452A,
                     0x500904E6,
                     0x5009fEB6,
                     0x50092C62,
                     0x5009EE30,
                     0x5009DE72,

                     0x9121000C,   # stw r9, 12(r1) ; Store P3, P4
                     0x60000000,   # Some nops for good measure
                     0x60000000,
                     0x60000000,
                     0x60000000,
                     0x60000000,
                     0x60000000,
                     0x60000000],

          0x28b618: [0x60000000]}  # nop ; Don't exit on Z

p_multirom = {0x28b560: [0x701f1000],      # andi. r31, r0, 0x1000 ; Exit check
              0x28b4c8: [0x60000000],      # nop ; Null reference on snesticle exit
              0x27cb7c: [0x60000000] * 7,  # nop * 7 ; More
              0x28aef8: [0x60000000],      # nop ; More
              0x19d260: [0x3c608062,       # lis  r3, 0x8062
                         0x6063aa8c,       # ori  r3, r3, 0xaa8c ; Pointer to SNES memory
                         0x80c30014,       # lwz  r6, 0x14(r3)   ; Read joypad settings
                         0x80a30010,       # lwz  r5, 0x10(r3)   ; Read game file name
                         0x3c808049,       # lis  r4, 0x8049
                         0x608463ac,       # ori  r4, r4, 0x63ac ; Pointer to real file name
                         0x90a40000,       # stw  r5, 0(r4)      ; Store game file name
                         0x3c608028,       # lis  r3, 0x8028
                         0x6063e560,       # ori  r3, r3, 0xe560 ; Pointer to exit check
                         0x3c806000,       # lis  r4, 0x6000     ; Create NOP
                         0x90830000,       # stw  r4, 0(r3)      ; Disable exit check

                         0x39430004,       # addi r10, r3, 4     ; Pointer to joypad code
                         0x39600004,       # addi r11, r0, 4     ; Loop index
                                          # loop:
                         0x54c6403e,       # rlwinm r6, r6, 8, 0, 31 ; Rotate 8 bits
                         0x70c700ff,       # andi. r7, r6, 0xff  ; Check lower 8 bits
                         0x40820010,       # bne not_off

                         0x3d206129,       # lis r9, 0x6129
                         0x6129ffff,       # ori r9, r9, 0xffff  ; Create ori r9, r9, 0xffff
                         0x912a001c,       # stw r9, 0x1c(r10)
                                          # not_off:
                         0x70e70002,       # andi. r7, r7, 2
                         0x41820048,       # beq not_literal

                         0x7D8C6278,       # xor  r12, r12, r12
                         0x698C4CAC,       # xori r12, r12, 0x4cac
                         0xB18A0002,       # sth  r12, 2(r10)
                         0x698C0986,       # xori r12, r12, 0x0986
                         0xB18A0006,       # sth  r12, 6(r10)
                         0x698C41CC,       # xori r12, r12, 0x41cc
                         0xB18A000A,       # sth  r12, 10(r10)
                         0x698C3908,       # xori r12, r12, 0x3908
                         0xB18A000E,       # sth  r12, 14(r10)
                         0x698CC3D8,       # xori r12, r12, 0xc3d8
                         0xB18A0012,       # sth  r12, 18(r10)
                         0x698CCA16,       # xori r12, r12, 0xca16
                         0xB18A0016,       # sth  r12, 22(r10)
                         0x698CD252,       # xori r12, r12, 0xd252
                         0xB18A001A,       # sth  r12, 26(r10)
                         0x698CFA10,       # xori r12, r12, 0xfa10
                         0xB18A001E,       # sth  r12, 30(r10)
                                          # not_literal:
                         0x396bffff,       # subi r11, r11, 1    ; Decrement loop index
                         0x716b0007,       # andi. r11, r11, 7   ; Silly 0 check
                         0x4182000c,       # beq exit_loop
                         0x394a0028,       # addi r10, r10, 40   ; Next joypad
                         0x4bffff8c,       # b loop
                                          # exit_loop:
                         0x38800100,       # addi r4, r0, 0x0100
                         0x4822d721,       # bl ICInvalidateRange
                         0x4bffff48]}      # b snesticle
literal = [0x5009452A,
           0x500904E6,
           0x50093DEE,
           0x5009FE36,
           0x50093420,
           0x5009E672,
           0x50091C62]

p_literal_1 = {0x28b564: [0x54094CAC] + literal}
p_literal_2 = {0x28b58c: [0x50094CAC] + literal}
p_literal_3 = {0x28b5b4: [0x54094CAC] + literal}
p_literal_4 = {0x28b5dc: [0x50094CAC] + literal}

p_off_1 = {0x28b580: [0x6129ffff]}
p_off_2 = {0x28b5a8: [0x6129ffff]}
p_off_3 = {0x28b5d0: [0x6129ffff]}
p_off_4 = {0x28b5f8: [0x6129ffff]}

p_mapping1 = {'literal': p_literal_1, 'off': p_off_1}
p_mapping2 = {'literal': p_literal_2, 'off': p_off_2}
p_mapping3 = {'literal': p_literal_3, 'off': p_off_3}
p_mapping4 = {'literal': p_literal_4, 'off': p_off_4}

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


def draw_logo(text, basex=0):
    bitmap = []
    for _ in range(8):
        bitmap.append([1] * 128)
    for (x, y) in font.pixels(system_m8.system_m8, text, basex, 0):
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
        tmap[tile] = (tiles.index(tile) + 0x80).to_bytes(1, 'big')
    for (l, r) in substs.items():
        tmap[l] = (tiles.index(r) + 0x80).to_bytes(1, 'big')
    for g in games:
        game = g[2]
        if not keep_extensions:
            game = game[:-4]
        game = os.path.basename(game).upper()[:30]
        stream.write(b'\0\0\0\0')
        for ch in game:
            stream.write(tmap.get(ch, b'\0'))
            stream.write(b'\0')
        for x in range(30 - len(game)):
            stream.write(b'\0\0')

    for x in range((25 - (len(games) % 25)) % 25):
        stream.write(b'\0\0' * 32)
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
    a.add_argument('--p1', choices=['sensible', 'literal', 'off'],
                   help='controller 1 button mapping (default is sensible)')
    a.add_argument('--p2', choices=['sensible', 'literal', 'off'],
                   help='controller 2 button mapping (default is sensible)')
    a.add_argument('--p3', choices=['sensible', 'literal', 'off'],
                   help='controller 3 button mapping (default is sensible)')
    a.add_argument('--p4', choices=['sensible', 'literal', 'off'],
                   help='controller 4 button mapping (default is sensible)')
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
    if multirom and (args.p1 or args.p2 or args.p3 or args.p4):
        print('Warning: Controller mapping options are ignored when creating multiple rom iso,'
              ' controllers are configured from the rom selection menu instead.', file=sys.stderr)

    with open(args.source, 'rb') as source:
        with open(args.target, 'wb') as target:
            # Write boot.bin, bi2.bin and apploader.bin
            target.write(source.read(0x440 + 0x2000 + 0x1dbb8))
            target.write(b'\0' * 8)

            # Write main.dol
            source.seek(0x20000)
            mainstream = io.BytesIO()
            mainstream.write(source.read(0x4ffa00))

            patches = [p_main]
            if multirom:
                patches.append(p_multirom)
            else:
                patches.append(p_mapping1.get(args.p1, {}))
                patches.append(p_mapping2.get(args.p2, {}))
                patches.append(p_mapping3.get(args.p3, {}))
                patches.append(p_mapping4.get(args.p4, {}))

            for p in patches:
                for (k, v) in p.items():
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
                menudata.seek(0x5010)
                menudata.write(draw_logo("#FreeTheSNESticle", 16).getvalue()[16:])
                menudata.write(draw_logo("Preferences", 31).getvalue())
                source.seek(0x56e90ab2)
                menudata.seek(0x5800)
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
