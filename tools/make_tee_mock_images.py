"""Web images for the Red Pill Tee six-color mock (front + back on gray, 5700x3500 source, approved by Mike Oct 26 2026).
Writes store-img/demo/duck-tee_<color>_mock.{jpg,webp} (1600x982) and _mock-900.{jpg,webp} (900x553).
Usage: python3 tools/make_tee_mock_images.py /path/to/shirt-mock-2026-10-26"""
import os, sys
from PIL import Image
SRC = sys.argv[1] if len(sys.argv) > 1 else '/workspace/trd-reports/shirt-mock-2026-10-26'
KEYS = ['black', 'white', 'tiffany', 'hotpink', 'navy', 'gold']
os.makedirs('store-img/demo', exist_ok=True)
for k in KEYS:
    im = Image.open(os.path.join(SRC, 'trd-tee-%s.png' % k)).convert('RGB')
    for w, suf in ((1600, ''), (900, '-900')):
        h = round(w * im.height / im.width)
        r = im.resize((w, h), Image.LANCZOS)
        b = 'store-img/demo/duck-tee_%s_mock%s' % (k, suf)
        r.save(b + '.jpg', 'JPEG', quality=85, optimize=True, progressive=True, subsampling='4:2:0')
        r.save(b + '.webp', 'WEBP', quality=85, method=6)
        print(b, r.size, os.path.getsize(b + '.jpg'), os.path.getsize(b + '.webp'))
