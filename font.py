#!/usr/bin/env python3

def pixels(font, string, basex=0, basey=0, backup='?'):
    for c in string:
        o = ord(c)
        if o not in font[1]:
            o = ord(backup)
        character = font[1][o]
        width = character[0]
        lines = character[1]
        for y, line in enumerate(lines):
            for x, bit in enumerate(reversed(range(width))):
                if line & (1 << bit):
                    yield (basex + x, basey + y)
        basex += width


def fit_box(font, words, w, h, linespacing, backup='?'):
    fh = font[0]
    if fh > h:
        return (False, [])
    acc = words[0]
    lastacc = ''
    lasttw = 0
    tw = width(font, words[0], backup)

    while tw <= w:
        words = words[1:]
        if not words:
            return (True, [acc])
        lastacc = acc
        lasttw = tw
        acc += ' ' + words[0]
        tw += width(font, ' ' + words[0], backup)

    if lasttw > 0:
        (fits, lines) = fit_box(font, words, w, h - fh - linespacing, linespacing, backup)
        if fits:
            return (True, [lastacc] + lines)

    letters = list(words[0])
    words = words[1:]
    acc = lastacc + (' ' if lastacc else '') + letters[0]
    tw = lasttw + width(font, (' ' if lastacc else '') + letters[0], backup)

    while tw <= w:
        letters.pop(0)
        lastacc = acc
        lasttw = tw
        acc += letters[0]
        tw += width(font, letters[0], backup)

    remaining = ''.join(letters)
    (fits, lines) = fit_box(font, [remaining] + words, w, h - fh - linespacing, linespacing, backup)
    return (fits, [lastacc] + lines)


def pixels_box(font, string, basex, basey, w, h, linespacing=1, backup='?'):
    (fits, lines) = fit_box(font, string.split(' '), w, h, linespacing, backup)
    for line in lines:
        for p in pixels(font, line, basex, basey, backup):
            yield p
        basey += font[0] + linespacing


def width(font, string, backup='?'):
    total = 0
    for c in string:
        o = ord(c)
        if o not in font[1]:
            o = ord(backup)
        total += font[1][o][0]
    return total
