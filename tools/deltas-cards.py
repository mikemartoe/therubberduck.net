#!/usr/bin/env python3
"""Share cards for the Deltas date pages: images/deltas/og/MM-DD.png (1200x630).

Same card as the Deltas hub preview (images/brand/social-deltas-20261030.png): that image is the template,
its 'DELTAS' line and subtitle are painted over with the date and the drop count, in the same font
(DejaVu Sans Mono), sizes and colours. Brand line, duck, green bar, frame and domain are untouched.
Used as og:image / twitter:image on /deltas/MM-DD/ (tools/seo-deltas-build.py) and as the picture the
date page's share row offers. Run from the repo root:  python3 tools/deltas-cards.py   (idempotent)
"""
import importlib.util, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('dxb', os.path.join(HERE, 'seo-deltas-build.py'))
DX = importlib.util.module_from_spec(spec); spec.loader.exec_module(DX)   # data only; its main() is not run

TEMPLATE = 'images/brand/social-deltas-20261030.png'
OUT = 'images/deltas/og'
BG, GREEN, TEXT = (5, 10, 7), (0, 237, 57), (232, 244, 233)
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
BOOK = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'


def card(k):
    ds = DX.BYDAY[k]; name = DX.mmdd_name(k)
    yrs = sorted({d['dt'].year for d in ds})
    span = str(yrs[0]) if len(yrs) == 1 else '%d to %d' % (yrs[0], yrs[-1])
    im = Image.open(TEMPLATE).convert('RGB')
    dr = ImageDraw.Draw(im)
    dr.rectangle((405, 215, 1140, 425), fill=BG)              # old 'DELTAS' + subtitle
    big = 64
    while dr.textlength(name.upper(), font=ImageFont.truetype(BOLD, big)) > 700: big -= 2
    dr.text((421, 282), name.upper(), font=ImageFont.truetype(BOLD, big), fill=GREEN, anchor='ls')
    f = ImageFont.truetype(BOOK, 27)
    dr.text((421, 372), 'Q drop deltas: %d drop%s' % (len(ds), '' if len(ds) == 1 else 's'), font=f, fill=TEXT, anchor='ls')
    dr.text((421, 406), 'posted on this date, %s.' % span, font=f, fill=TEXT, anchor='ls')
    return im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for k in DX.DAYS:
        if only and k not in only: continue
        card(k).save(os.path.join(OUT, '%s.png' % k), optimize=True)
    print('deltas cards: %d in %s' % (len(only) or len(DX.DAYS), OUT))


if __name__ == '__main__':
    main()
