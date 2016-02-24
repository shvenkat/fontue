"""
Usage:
  fontue [options] add [-g GLYPHS] <source_font> <target_font> <new_font>
  --glyphs=GLYPH_SPEC
  --bbox               Bounding box of one of more glyphs
  --source-bbox=GLYPH_SPEC  Bounding box of source font
  --target-bbox=GLYPH_SPEC  Bounding box of target font
  --override
  --name=FONT_NAME

Arguments:
  <font>, <source_font>, <target_font>, <new_font>

Specifying glyphs:
  GLYPH_SPEC
"""

#!/usr/bin/env python

import argparse
import sys
import re
import os.path
import ipdb

try:
    import fontforge
    import psMat
except ImportError:
    sys.stderr.write('The required FontForge modules could not be loaded.\n')
    if sys.version_info.major > 2:
        sys.stderr.write('FontForge only supports Python 2. ' +
                         'Please run this script with the Python 2 ' +
                         'executable - e.g. "python2 %s"\n' %
                         (sys.argv[0],))
    else:
        sys.stderr.write('You need FontForge with Python bindings ' +
                         'for this script to work.\n')
    sys.exit(1)

def parse_args():
    description = "Add glyphs from a source font to a target font, " + \
                  "saving the result as an updated target font. " + \
                  "Requires FontForge with Python bindings."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('source_font',
                        help='source font file (provides glyphs)',
                        type=argparse.FileType('rb'))
    parser.add_argument('target_font',
                        help='target font file (needs glyphs)',
                        type=argparse.FileType('rb'))
    parser.add_argument('new_font',
                        help='new target font file (receives glyphs)')
    glyph_group = parser.add_mutually_exclusive_group(required=True)
    glyph_group.add_argument('--glyphs', help='names of glyphs to copy',
                             nargs='+', metavar='name')
    glyph_group.add_argument('--all-glyphs', help='copy all glyphs',
                             action='store_true')
    parser.add_argument('--overwrite',
                        help='replace glyphs in the target font',
                        action='store_true')
    parser.add_argument('--new-suffix',
                        help='suffix used to derive new target font name',
                        metavar='name_suffix')
    args = parser.parse_args()
    return args


def bounding_box(font, glyph=None):
    if isinstance(glyph, str):
        if glyph in font:
            return font[glyph].boundingBox()
        else:
            return None
    # elif isinstance(glyph, int):
    else:
        bbox = [0, 0, 0, 0]
        for glyph in font.glyphs():
            bb = font[glyph].boundingBox()
            bbox[0] = bb[0] if bb[0] < bbox[0] else bbox[0]
            bbox[1] = bb[1] if bb[1] < bbox[1] else bbox[1]
            bbox[2] = bb[2] if bb[2] > bbox[2] else bbox[2]
            bbox[3] = bb[3] if bb[3] > bbox[3] else bbox[3]
        return bbox


def copy_glyphs(glyphs, source_font, target_font, new_font, new_suffix,
                overwrite):
    target_font_em_original = target_font.em
    target_font.em = 2048
    target_font.encoding = 'ISO10646'

    # Rename font
    target_font.familyname += new_suffix
    target_font.fullname += new_suffix
    fontname, style = re.match("^([^-]*)(?:(-.*))?$",
                               target_font.fontname).groups()
    target_font.fontname = fontname + new_suffix.replace(' ', '')
    if style is not None:
        target_font.fontname += style
    target_font.appendSFNTName('English (US)', 'Preferred Family',
                               target_font.familyname)
    target_font.appendSFNTName('English (US)', 'Compatible Full',
                               target_font.fullname)

    # range(0x00, 0x17f) + range(0x2500, 0x2600):
    ipdb.set_trace()
    source_bb = source_font['block'].boundingBox()
    target_bb = [0, 0, 0, 0]
    target_font_width = 0

    # Find the biggest char width and height in the Latin-1 extended range and the box drawing range
    # This isn't ideal, but it works fairly well - some fonts may need tuning after patching
    for cp in range(0x00, 0x17f) + range(0x2500, 0x2600):
        try:
            bbox = target_font[cp].boundingBox()
        except TypeError:
            continue
        if not target_font_width:
            target_font_width = target_font[cp].width
        if bbox[0] < target_bb[0]:
            target_bb[0] = bbox[0]
        if bbox[1] < target_bb[1]:
            target_bb[1] = bbox[1]
        if bbox[2] > target_bb[2]:
            target_bb[2] = bbox[2]
        if bbox[3] > target_bb[3]:
            target_bb[3] = bbox[3]

    # Find source and target size difference for scaling
    x_ratio = (target_bb[2] - target_bb[0]) / (source_bb[2] - source_bb[0])
    y_ratio = (target_bb[3] - target_bb[1]) / (source_bb[3] - source_bb[1])
    scale = psMat.scale(x_ratio, y_ratio)

    # Find source and target midpoints for translating
    x_diff = target_bb[0] - source_bb[0]
    y_diff = target_bb[1] - source_bb[1]
    translate = psMat.translate(x_diff, y_diff)
    transform = psMat.compose(scale, translate)
    sys.stderr.write("Source: %i %i %i %i\n" % (source_bb[0], source_bb[1], source_bb[2], source_bb[3]))
    sys.stderr.write("Target: %i %i %i %i\n" % (target_bb[0], target_bb[1], target_bb[2], target_bb[3]))
    sys.stderr.write("Offset: %.2f %.2f, Ratio: %.2f %.2f\n" % (x_diff, y_diff, x_ratio, y_ratio))
    # print(scale)
    # print(translate)
    # print(transform)

    # Create new glyphs from symbol font
    for source_glyph in source_font.glyphs():
        if source_glyph == source_font['block']:
            # Skip the symbol font block glyph
            continue

        # Select and copy symbol from its encoding point
        source_font.selection.select(source_glyph.encoding)
        source_font.copy()

        # Select and paste symbol to its unicode code point
        target_font.selection.select(source_glyph.unicode)
        target_font.paste()

        # Transform the glyph
        target_font.transform(transform)

        # Reset the font's glyph width so it's still considered monospaced
        target_font[source_glyph.unicode].width = target_font_width

    target_font.em = target_font_em_original

    # Generate patched font
    extension = os.path.splitext(target_font.path)[1]
    if extension.lower() not in ['.ttf', '.otf']:
        # Default to OpenType if input is not TrueType/OpenType
        extension = '.otf'
    target_font.generate('{0}{1}'.format(target_font.fullname, extension))


def main():
    args = parse_args()
    source_font = fontforge.open(args.source_font.name)
    target_font = fontforge.open(args.target_font.name)
    new_font = args.new_font
    glyphs = source_font.glyphs() if args.all_glyphs else args.glyphs
    new_suffix = args.new_suffix if args.new_suffix else ''
    overwrite = args.overwrite
    copy_glyphs(glyphs, source_font, target_font, new_font,
                new_suffix, overwrite)
    args.source_font.close()
    args.target_font.close()


if __name__ == '__main__':
    main()
