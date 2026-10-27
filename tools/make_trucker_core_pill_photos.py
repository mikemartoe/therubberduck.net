"""Trucker Hat regular colors Charcoal / Black, Heather Grey / Black, Heather Grey / White: the real Printful product photos
(store-img/duck-trucker-hat_<c>.jpg, read only, never changed) get the approved red pill on the bill, by the same method as the
12 signed front photos (tools/signed_hat_pill.py, art tools/art/red-pill.png). Placement is measured per image; any landmark more
than 4px off the signed-trucker group reference falls back to it (same rule as the signed run). REF is the group median the signed
trucker run used (tools/make_signed_hat_front_photos.py), so all 9 trucker photos share one placement rule. Oct 26 2026.
Usage, from the repo root:  python3 tools/make_trucker_core_pill_photos.py   -> store-img/duck-trucker-hat-f_<c>.{jpg,webp}"""
import os, sys, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'store-img')
sys.path.insert(0, HERE)
import signed_hat_pill as sp
REF = {'xl': 126.0, 'xr': 677.5, 'sl': 542.5, 'el': 678.0, 'sc': 547.0, 'ec': 676.0, 'sr': 542.0, 'er': 677.5}
for c in ('charcoal-black', 'heather-grey-black', 'heather-grey-white'):
    a = np.asarray(Image.open(os.path.join(D, 'duck-trucker-hat_%s.jpg' % c)).convert('RGB')).astype(float)
    raw = sp.measure(a, 'trk'); m = sp.measure(a, 'trk', REF); q = sp.place(m)
    im = Image.fromarray(np.clip(sp.apply(a, q), 0, 255).round().astype('uint8'))
    f = os.path.join(D, 'duck-trucker-hat-f_%s' % c)
    im.save(f + '.jpg', quality=90, optimize=True, progressive=True); im.save(f + '.webp', quality=84, method=6)
    print(c, 'raw', raw, '\n   used', m)
    print('   pill w/crown %.3f  ratio %.2f  seam:edge gap %.1f:%.1f = %.2f  tilt %.4f  arch %.2fpx  centre (%.1f, %.1f)' % (
        q['W'] / q['CW'], q['W'] / q['H'], q['seam_gap'], q['edge_gap'], q['seam_gap'] / q['edge_gap'], q['tilt'], q['arch'], q['cx'], q['cy']))
