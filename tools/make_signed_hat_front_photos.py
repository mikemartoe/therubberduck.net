"""Signed hat card photos = the approved FRONT-view product photos of the regular hats (Mike, Oct 26 2026: front views only; the
11/500 signature shows only as the small preview on the card back and the listing page). Usage, from the repo root:
    python3 tools/make_signed_hat_front_photos.py
Dad hat: store-img/duck-dad-hat_<c>_product.{jpg,webp} copied byte for byte to store-img/signed-dad-hat_<c>.{jpg,webp}.
Trucker: Black = the real Printful mockup duck-trucker-hat_black-white (Richardson 112 Black / White, the variant sold as Black).
White, Navy, Gold, Tiffany Blue and Hot Pink: Printful has no such Richardson 112 blank, so (same method as
tools/make_dad_hat_special_photos.py) the real Printful Heather Grey/White mockup is recolored: only the front crown and bill fabric
is re-tinted; the duck embroidery, mesh, eyelets, background and shadow are the mockup's own pixels, nothing moved or scaled.
Colors are matched to the dad-hat photo of the same color so S1 and S2 line up.
All 12 then get the approved red pill on the bill (tools/signed_hat_pill.py; art tools/art/red-pill.png). The regular
duck-dad-hat_<c>_product photos are read only, never changed."""
import os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'store-img')
import numpy as np, sys

from PIL import Image, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signed_hat_pill as sp
COLS = ('black', 'white', 'navy', 'gold', 'tiffany', 'hotpink')
OUT = D
L = lambda f: np.asarray(Image.open(os.path.join(D, f)).convert('RGB')).astype(float)
A = L('duck-trucker-hat_heather-grey-white.jpg'); B = L('duck-trucker-hat_black-white.jpg')
lum = lambda x: x @ [0.299, 0.587, 0.114]
diff = np.abs(A - B).sum(2); la = lum(A)
F = nd.binary_fill_holes(nd.binary_closing(diff > 150, iterations=3))
F = F & ((diff > 90) | (la > nd.uniform_filter(la, 9) + 10))   # stitches (bright on both) stay in, to be re-tinted tonal
# the duck: keep only heather-grey-looking fabric inside its box, everything else (all threads) stays real
box = np.zeros(F.shape, bool); box[280:500, 270:540] = True
r, g, b = A[..., 0], A[..., 1], A[..., 2]; la = lum(A)
heather = (np.abs(r - g) < 12) & (np.abs(b - r) < 14) & (la > 105) & (la < 225)
emb = box & ~heather
emb = nd.binary_opening(emb, iterations=1)
lab, n = nd.label(emb); sz = nd.sum(emb, lab, range(1, n + 1)); emb = np.isin(lab, 1 + np.where(sz > 150)[0])
sil = nd.binary_fill_holes(nd.binary_closing(emb, iterations=4))   # the whole duck silhouette
emb = nd.binary_fill_holes(nd.binary_closing(emb, iterations=1))     # threads + fully enclosed gaps stay real; open notches are fabric
F = F & ~emb
lab, n = nd.label(F); s = nd.sum(F, lab, range(1, n + 1)); F = np.isin(lab, 1 + np.where(s > 40)[0])
# shading: heather speckle smoothed away (normalized blur inside the fabric), folds and light kept
Fm = F.astype(float)
def nblur(x, sg): return nd.gaussian_filter(x * Fm, sg) / np.maximum(nd.gaussian_filter(Fm, sg), 1e-3)
# low-frequency light from the grey mockup (big blur kills the heather mottling), fine seams/weave from the black mockup
# (solid twill, no heather), and the bill's contrast stitching from the grey mockup as tonal (lighter) thread.
ref = np.median(la[F])
low = nblur(la, 7.0) / ref
lb = lum(B); detB = np.clip(nblur(lb, 0.6) / np.maximum(nblur(lb, 4.0), 8), 0.55, 1.6) ** 0.55
band = nd.gaussian_filter(nd.binary_dilation(sil, iterations=7).astype(float), 2)   # the black mockup's duck has a light outline: no weave detail from it there
detB = detB * (1 - band) + band
stitch = np.clip(la - nblur(la, 3.0) - 14, 0, 80) / ref
S = low * detB
tex = stitch
REG = (slice(170, 260), slice(200, 300))              # left front panel, same spot on both hats
dadS = {'white': 'duck-dad-hat_white_product.jpg', 'navy': 'duck-dad-hat_navy_product.jpg', 'gold': 'duck-dad-hat_gold_product.jpg',
        'tiffany': 'duck-dad-hat_tiffany_product.jpg', 'hotpink': 'duck-dad-hat_hotpink_product.jpg'}
TRK = {'black': B}
m = np.asarray(Image.fromarray((F * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7))).astype(float)[..., None] / 255
for k, f in dadS.items():
    dad = L(f); want = np.median(dad[REG].reshape(-1, 3), 0)
    sreg = np.median(S[REG][F[REG]])
    tgt = want / sreg
    rec = np.clip(tgt[None, None] * S[..., None] + 255 * 0.55 * tex[..., None] * (1 - tgt[None, None] / 290), 0, 255)
    out = A * (1 - m) + rec * m
    TRK[k] = out
    print(k, want.round(), tgt.round())

# ---- red pill on the bill, all 12 (Mike, Oct 26 2026): placement measured per image, see tools/signed_hat_pill.py
def finish(kind, stem, arrs):
    ms = {c: sp.measure(arrs[c], kind) for c in COLS}
    ref = {k: float(np.median([m[k] for m in ms.values()])) for k in ms['black']}
    for c in COLS:
        q = sp.place(sp.measure(arrs[c], kind, ref))
        im = Image.fromarray(np.clip(sp.apply(arrs[c], q), 0, 255).round().astype('uint8'))
        f = os.path.join(OUT, '%s_%s' % (stem, c))
        im.save(f + '.jpg', quality=90, optimize=True, progressive=True); im.save(f + '.webp', quality=84, method=6)
        print(stem, c, 'pill w/crown %.3f  ratio %.2f  seam:edge gap %.1f:%.1f = %.2f  tilt %.3f  arch %.1fpx  centre (%.1f, %.1f)' % (
            q['W'] / q['CW'], q['W'] / q['H'], q['seam_gap'], q['edge_gap'], q['seam_gap'] / q['edge_gap'], q['tilt'], q['arch'], q['cx'], q['cy']))
finish('dad', 'signed-dad-hat', {c: L('duck-dad-hat_%s_product.jpg' % c) for c in COLS})
finish('trk', 'signed-trucker-hat', TRK)
