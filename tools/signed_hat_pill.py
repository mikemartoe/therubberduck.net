"""Red pill on the bill of the signed-hat front photos (Mike, Oct 26 2026).
The approved trademark pill art (tools/art/red-pill.png, the same pill_crop art used by the hat demo stills and the premium mockups),
placed by the approved navy-still rules, measured per image from landmarks (never by eye):
  width = 0.335 x crown width; shape 3.9:1 (the approved ratio); centred on the bill centre line;
  seam gap : edge gap = 0.45 along the centre line (closer to the brim seam than the bill edge);
  tilt and arch follow the bill: the pill centre line is placed at the same seam-gap rule at its two ends, so it bends with the bill
  (columns shifted vertically only, never stretched); glossy printed look and soft contact shadow as on the approved still."""
import os, cv2, numpy as np
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
PILL_RATIO, PILL_AR, GAP = 0.335, 3.9, 0.45
G = {'dad': dict(seam=(420, 452), edge=(570, 625), crow=(436, 446)),
     'trk': dict(seam=(536, 556), edge=(662, 690), crow=(496, 504))}
_art = None
def art():
    global _art
    if _art is None:
        p = cv2.imread(os.path.join(HERE, 'art', 'red-pill.png'), cv2.IMREAD_UNCHANGED)
        m = (p[..., 3] > 128).astype(np.uint8) * 255
        cn, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); f = np.zeros_like(m); cv2.drawContours(f, cn, -1, 255, -1)
        p[..., 3] = np.maximum(p[..., 3], cv2.erode(f, np.ones((3, 3), np.uint8)))   # solid body, soft rim (as comp5)
        _art = cv2.cvtColor(p, cv2.COLOR_BGRA2RGBA)
    return _art

def landmarks(a, kind):
    """a: HxWx3 float RGB. Returns crown (xl, xr), cx, seam(x), edge(x) functions (top surface of the bill)."""
    g = G[kind]; L = nd.gaussian_filter(a @ [0.299, 0.587, 0.114], (1.2, 2))
    rows = L[g['crow'][0]:g['crow'][1]].mean(0); gx = np.abs(np.gradient(rows))
    xl = int(np.argmax(gx[40:400])) + 40; xr = int(np.argmax(gx[400:780])) + 400
    def col(x, w):
        return L[w[0]:w[1], int(round(x)) - 3:int(round(x)) + 4].mean(1)
    seam = lambda x: g['seam'][0] + int(np.argmin(col(x, g['seam'])))
    edge = lambda x: g['edge'][0] + int(np.argmax(np.abs(np.gradient(col(x, g['edge'])))))
    return xl, xr, seam, edge

def measure(a, kind, ref=None):
    """Landmarks at the pill's centre and both ends. ref = group medians; any landmark >4px off (low-contrast colours such as white,
    or a bill stitch row mistaken for the edge) falls back to the group value, since all colours share one Printful template."""
    xl, xr, seam, edge = landmarks(a, kind)
    m = dict(xl=xl, xr=xr)
    if ref:
        for k in ('xl', 'xr'):
            if abs(m[k] - ref[k]) > 4: m[k] = ref[k]
    CW = m['xr'] - m['xl']; cx = (m['xl'] + m['xr']) / 2; W = PILL_RATIO * CW
    for tag, x in (('l', cx - W / 2), ('c', cx), ('r', cx + W / 2)):
        m['s' + tag], m['e' + tag] = seam(x), edge(x)
    if ref:
        for k in ('sl', 'sc', 'sr', 'el', 'ec', 'er'):
            if abs(m[k] - ref[k]) > 4: m[k] = ref[k]
    return m

def place(m):
    CW = m['xr'] - m['xl']; cx = (m['xl'] + m['xr']) / 2; W = PILL_RATIO * CW; H = W / PILL_AR
    yc = {}
    for t in ('l', 'c', 'r'):
        s, e = m['s' + t], m['e' + t]; sg = GAP / (1 + GAP) * (e - s - H); yc[t] = s + sg + H / 2
    tilt = (yc['r'] - yc['l']) / W                       # px per px
    arch = (yc['l'] + yc['r']) / 2 - yc['c']             # >0: ends sit lower (bill curves down at the sides)
    sg = GAP / (1 + GAP) * (m['ec'] - m['sc'] - H)
    return dict(cx=cx, cy=yc['c'], W=W, H=H, tilt=tilt, arch=arch, CW=CW, seam_gap=sg, edge_gap=m['ec'] - m['sc'] - H - sg)

def apply(a, q, S=4):
    """Composite the pill onto a (HxWx3 float RGB) by plan q; returns new array."""
    W, H = q['W'], q['H']
    p = cv2.resize(art(), (int(round(W * S)), int(round(H * S))), interpolation=cv2.INTER_AREA).astype(np.float32)
    pad = 12
    x0 = int(np.floor(q['cx'] - W / 2)) - pad; x1 = int(np.ceil(q['cx'] + W / 2)) + pad
    y0 = int(np.floor(q['cy'] - H / 2 - abs(q['arch']) - abs(q['tilt']) * W / 2)) - pad; y1 = int(np.ceil(q['cy'] + H / 2 + abs(q['arch']) + abs(q['tilt']) * W / 2)) + pad
    X, Y = np.meshgrid((np.arange((x1 - x0) * S) + 0.5) / S + x0, (np.arange((y1 - y0) * S) + 0.5) / S + y0)
    u = (X - q['cx']) / (W / 2)
    ycl = q['cy'] + q['arch'] * u ** 2 + q['tilt'] * (X - q['cx'])
    mx = ((X - (q['cx'] - W / 2)) * S - 0.5).astype(np.float32); my = ((Y - (ycl - H / 2)) * S - 0.5).astype(np.float32)
    big = cv2.remap(p, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    sm = cv2.resize(big, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    al = sm[..., 3:4] / 255.; rgb = np.where(al > 1e-3, sm[..., :3] / np.maximum(al, 1e-3), 0)
    out = a.copy(); reg = out[y0:y1, x0:x1]
    sh = cv2.GaussianBlur(np.roll(np.roll(al[..., 0], 3, 0), 1, 1), (0, 0), 2.6) * 0.42   # soft contact shadow (approved still)
    reg = reg * (1 - sh[..., None])
    reg = reg * (1 - al) + np.clip(rgb, 0, 255) * al
    out[y0:y1, x0:x1] = reg
    return out
