# fn22snesticle.py

Scripts for producing a SNESticle ISO from a Fight Night Round 2 ISO and any
SNES ROM.

## Background

Fight Night Round 2 is a boxing game by Electronic Arts. The Gamecube version of
which includes the SNES game Super Punch-Out!!, playable through SNES emulation.
Data mining has shown that the DVD contains the strings "SNESticle" and
"Copyright (c) 1997-2004 Icer Addis", suggesting that this emulator is in fact
SNESticle, the much anticipated but never released follow-up to NESticle.

This script extracts SNESticle from a Fight Night Round 2 ISO (US version) and
produces a new ISO containing just SNESticle and a SNES ROM (Super Punch-Out!!
or a SNES ROM of your choice). It also patches the joypad emulation to fix some
issues and create a more logical button layout.

## Requirements

fn22snesticle.py requires Python 3 and the pillow (PIL) module.

## Usage

There are quite a few options but most have sensible defaults, just check the
help screen:

    ./fn22snesticle.py --help

The simplest invocation would look something like this:

    ./fn22snesticle.py fightnight2.iso superpunchout.iso

This will take SNESticle and the Super Punch-Out!! ROM directly from
fightnight2.iso and use them to produce superpunchout.iso.

More interestingly, you can use the --rom option to include a different SNES
ROM:

    ./fn22snesticle.py --rom smw.sfc fightnight2.iso smw.iso

This will produce an ISO containing SNESticle and the ROM smw.sfc (whatever that
might mean).

While you are at it, you probably want to replace the Fight Night 2 banner
graphic that shows up next to the ISO in your loader. You can use the included
snesticle.png for a minimalistic NESticle style logo, or you can go all out and
create custom graphics for each SNES ROM. Pretty much any image format should
work, but png is the only one that has been thoroughly tested.

    ./fn22snesticle.py --rom smw.sfc --banner snesticle.png fightnight2.iso smw.iso

The rest of the options are for changing some of the string values that may or
may not be visible in your loader.

## The a2bnr.py utility

A banner is a 96x32 bitmap plus a couple of text strings describing the game. It
shows up in the Gamecube OS, as well as in loaders like Swiss and in emulators
like Dolphin. a2bnr.py is a Python module that is used by fn22snesticle.py to
create a Gamecube banner file from a png, but a2bnr.py can also be used as a
stand-alone program to create a new banner from an image file or to modify an
existing banner file. A typical invocation would look like this:

    ./a2bnr.py --image myimage.png mybanner.bnr

This will convert myimage.png to the banner format and write it to
mybanner.bnr. If mybanner.bnr already exists, this will only overwrite the
bitmap portion of the file, leaving the text strings intact. Similarly, it is
possible to replace just (a subset of) the text strings in an existing banner
file:

    ./a2bnr.py --game-name "My game" --developer "I made this" someoldbanner.bnr

This will overwrite the game name and developer fields of someoldbanner.bnr
without touching the bitmap or the other text strings.

When creating a new bnr file, the --image option is required but everything else
is optional. a2bnr.py will accept any image format that PIL can understand.

## SNESticle considerations

### Joypad emulation

SNESticle maps the Gamecube buttons to SNES buttons in a very literal way, ie A
on the Gamecube controller becomes A on the SNES controller. This works for
Super Punch Out but is useless for most games, so the script patches the code to
map buttons based on physical location instead:

| GC button | SNES button|
|-----------|------------|
| A         | B          |
| B         | Y          |
| X         | A          |
| Y         | X          |
| Start     | Start      |
| Z         | Select     |

### Compatibility etc

At the time of writing, little is known about the features or accuracy of
SNESticle. It happily accept standard SNES ROMS with or without the header (ie
SMC or SFC files) and it runs a lot of games with no trouble. It does not seem
to support external chips like the DSP or Super FX.

## Further reading

More information on this project can be found at
https://www.update.uu.se/~johannes/snesticle/

