"""Web images for the Red Pill Tee six-color mock (front + back on gray, 5700x3500 source, approved by Mike Oct 26 2026).
Writes store-img/demo/duck-tee_<color>_mock.{jpg,webp} (1600x982) and _mock-900.{jpg,webp} (900x553).
--cards-only (Oct 26 2026, approved by Mike): the merch.html store card shows the FRONT of the shirt large on the card face and the BACK
(slogan + QR) on the flip side, per color:
  store-img/demo/duck-tee_<color>_front.{jpg,webp} (800x1300): a tight crop of the front shirt from the mock. The shirt fills the width
    with a small even margin; the frame is object-fit:cover, so desktop (about 0.85 wide:tall) trims only gray above and below and mobile
    (about 0.65) shows the whole shirt. Where the crop runs past the mock's top or bottom, the mock's own edge gray is carried out.
  store-img/demo/duck-tee_<color>_back.{jpg,webp} (800x620): the back shirt's upper body, centered on the slogan and the QR code.
The old duck-tee_<color>_card files (whole mock on a tall canvas) are still written for anything that links to them.
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

def crop_pad(im, x0, y0, x1, y1):
    """Crop im to the box (source pixels); rows above/below the image are its own edge gray (smoothed sideways)."""
    W, H = im.size
    a = np.asarray(im, dtype=np.float32)
    out = np.empty((y1 - y0, x1 - x0, 3), np.float32)
    def edge(rows):
        e = Image.fromarray(np.clip(rows.mean(0), 0, 255).astype(np.uint8)[None].repeat(8, 0))
        return np.asarray(e.filter(ImageFilter.GaussianBlur(120)), np.float32)[4]
    top, bot = edge(a[:20, x0:x1]), edge(a[-20:, x0:x1])
    ys, ye = max(y0, 0), min(y1, H)
    out[ys - y0:ye - y0] = a[ys:ye, x0:x1]
    out[:ys - y0] = top
    if ye < y1:
        out[ye - y0:] = bot
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))

S = 5700 / 1024  # mock coordinates below are in the 1024-wide web copy
FRONT_BOX = (67, 297, 420 / (800 / 1300))  # x0, center y, width -> height; front shirt spans about x 80-475, y 70-545
BACK_BOX = (546, 252, 380 / (800 / 620))   # back print: slogan about y 175-210, QR about y 220-330, shirt x 528-945

def box(x0, cy, w_web, h_web):
    return (round(x0 * S), round((cy - h_web / 2) * S), round((x0 + w_web) * S), round((cy + h_web / 2) * S))

for k in KEYS:
    im = Image.open(os.path.join(SRC, 'trd-tee-%s.png' % k)).convert('RGB')
    for name, (x0, cy, h), wweb, size in (('front', FRONT_BOX, 420, (800, 1300)), ('back', BACK_BOX, 380, (800, 620))):
        c = crop_pad(im, *box(x0, cy, wweb, h)).resize(size, Image.LANCZOS)
        b = 'store-img/demo/duck-tee_%s_%s' % (k, name)
        c.save(b + '.jpg', 'JPEG', quality=86, optimize=True, progressive=True, subsampling='4:2:0')
        c.save(b + '.webp', 'WEBP', quality=86, method=6)
        print(b, c.size, os.path.getsize(b + '.jpg'), os.path.getsize(b + '.webp'))

for k in KEYS:
    c = card(Image.open(os.path.join(SRC, 'trd-tee-%s.png' % k)).convert('RGB'))
    b = 'store-img/demo/duck-tee_%s_card' % k
    c.save(b + '.jpg', 'JPEG', quality=85, optimize=True, progressive=True, subsampling='4:2:0')
    c.save(b + '.webp', 'WEBP', quality=85, method=6)
    print(b, c.size, os.path.getsize(b + '.jpg'), os.path.getsize(b + '.webp'))
