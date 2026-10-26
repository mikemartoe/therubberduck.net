"""Web images for the Red Pill Tee six-color mock (front + back on gray, 5700x3500 source, approved by Mike Oct 26 2026).
Writes store-img/demo/duck-tee_<color>_mock.{jpg,webp} (1600x982) and _mock-900.{jpg,webp} (900x553).
Also writes store-img/demo/duck-tee_<color>_card.{jpg,webp} (800x1600) for the merch.html store card: the same mock, full width and
uncropped, centered on a tall canvas whose gray is the mock's own gray carried up and down from its top and bottom edges and eased into
one flat gray (CARD_BG, also the card frame's background), so a portrait card frame shows the whole photo with no bands or seams.
Usage: python3 tools/make_tee_mock_images.py /path/to/shirt-mock-2026-10-26 [--cards-only]"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SRC = ARGS[0] if ARGS else '/workspace/trd-reports/shirt-mock-2026-10-26'
CARD_W, CARD_H, CARD_EASE = 800, 1600, 420
CARD_BG = (92, 91, 92)  # keep in step with the .item[data-slug="duck-tee"] .photo background in merch.html (#5c5b5c)
KEYS = ['black', 'white', 'tiffany', 'hotpink', 'navy', 'gold']
os.makedirs('store-img/demo', exist_ok=True)
for k in ([] if '--cards-only' in sys.argv else KEYS):
    im = Image.open(os.path.join(SRC, 'trd-tee-%s.png' % k)).convert('RGB')
    for w, suf in ((1600, ''), (900, '-900')):
        h = round(w * im.height / im.width)
        r = im.resize((w, h), Image.LANCZOS)
        b = 'store-img/demo/duck-tee_%s_mock%s' % (k, suf)
        r.save(b + '.jpg', 'JPEG', quality=85, optimize=True, progressive=True, subsampling='4:2:0')
        r.save(b + '.webp', 'WEBP', quality=85, method=6)
        print(b, r.size, os.path.getsize(b + '.jpg'), os.path.getsize(b + '.webp'))

def card(im):
    w = CARD_W
    h = round(w * im.height / im.width)
    r = np.asarray(im.resize((w, h), Image.LANCZOS), dtype=np.float32)
    out = np.empty((CARD_H, w, 3), np.float32)
    out[:] = CARD_BG
    y0 = (CARD_H - h) // 2
    out[y0:y0 + h] = r
    flat = np.array(CARD_BG, np.float32)
    def edge(rows):  # the mock's edge gray, smoothed sideways so no shirt or noise detail is smeared outward
        e = Image.fromarray(np.clip(rows.mean(0), 0, 255).astype(np.uint8)[None].repeat(8, 0))
        return np.asarray(e.filter(ImageFilter.GaussianBlur(40)), np.float32)[4]
    top, bot = edge(r[:6]), edge(r[-6:])
    for d in range(1, y0 + 1):
        t = min(d / CARD_EASE, 1.0); t = t * t * (3 - 2 * t)
        out[y0 - d] = top * (1 - t) + flat * t
    for d in range(1, CARD_H - y0 - h + 1):
        t = min(d / CARD_EASE, 1.0); t = t * t * (3 - 2 * t)
        out[y0 + h - 1 + d] = bot * (1 - t) + flat * t
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))

for k in KEYS:
    c = card(Image.open(os.path.join(SRC, 'trd-tee-%s.png' % k)).convert('RGB'))
    b = 'store-img/demo/duck-tee_%s_card' % k
    c.save(b + '.jpg', 'JPEG', quality=85, optimize=True, progressive=True, subsampling='4:2:0')
    c.save(b + '.webp', 'WEBP', quality=85, method=6)
    print(b, c.size, os.path.getsize(b + '.jpg'), os.path.getsize(b + '.webp'))
