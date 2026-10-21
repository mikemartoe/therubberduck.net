#!/usr/bin/env python3
"""
memes-intake.py — take a folder of images / GIFs / videos into the meme dump.

    python3 tools/memes-intake.py <folder>

For every file in <folder> that is not already in memes/data/memes.json (matched
on sha256 first, then on filename) it:

  * keeps the original untouched — copies it into memes/staging/ if it came from
    somewhere else, and records that path as "original"
  * writes a web-size derivative into memes/web/<id>.<ext>
  * reads the tagging fields the page already uses: kind, family, orientation,
    ratio, palette, brightness, detail, textLikely, animated, width, height,
    bytes, sha256, duration_s
  * builds topics from the filename, the OCR text (tesseract) and the image's
    own colour/light/detail character
  * appends one record to memes/data/memes.json, leaving every existing record
    exactly as it was

Safe to run again over the same folder: the second run adds nothing.

    python3 tools/memes-intake.py memes/staging --no-ocr     # fast
    python3 tools/memes-intake.py <folder> --dry-run         # report only

Maintenance: --rebuild re-derives memes/web/ for records already in the JSON
(used to bring an older set up to the current web-size targets). It never
touches memes/staging/ or the tagging fields.
"""
import argparse, colorsys, datetime, hashlib, json, os, re, shutil, subprocess, sys
from collections import Counter

from PIL import Image, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "memes/data/memes.json")
STAGING = os.path.join(ROOT, "memes/staging")
WEB = os.path.join(ROOT, "memes/web")
WORK = os.path.join(ROOT, ".work")
OCR_CACHE = os.path.join(WORK, "ocr_cache_intake.json")

IMG_EXT = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "tif", "tiff"}
VID_EXT = {"mp4", "webm", "mov", "m4v"}
STILL_EXT = {"jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff"}

MAX_STILL = 1600        # long edge
STILL_BUDGET = 350_000  # bytes, target ceiling for a still
GIF_MAX_W = 800
GIF_BUDGET = 2_500_000

# ---- faces --------------------------------------------------------------
# Still images only. GIFs and videos get faces = null (unknown), never 0: a
# frame we did not scan is not a frame with nobody in it.
FACE_CASCADE_PATH = os.path.join(ROOT, "tools/cascades/face.xml")
FACE_EXT = {"jpg", "jpeg", "png", "webp"}
FACE_LONG = 900         # scan a copy whose long edge is <= this
FACE_MIN = 28           # smallest box worth counting
FACE_SCALE, FACE_NEIGHBOURS = 1.08, 6
FACE_TAGS = ("face", "one face", "two faces", "crowd")
_FACE_CASCADE = None
_face_warned = False

# ---------------------------------------------------------------- vocabulary
ENTITY_TAGS = {
 "epstein": ["epstein", "ghislaine", "maxwell"],
 "jfk": ["jfk", "kennedy", "oswald"],
 "diana": ["diana", "dodi", "princess"],
 "peta": ["peta"], "fema": ["fema"],
 "covid": ["covid", "corona", "pandemic", "plandemic", "vaccine", "vaxx"],
 "election": ["election", "ballot", "vote", "voting", "elector"],
 "aliens": ["alien", "ufo", "uap", "extraterrest"],
 "spielberg": ["spielberg"], "smokey": ["smokey", "smokey-bear"],
 "army": ["army", "soldier", "military", "troop"],
 "flag": ["flag", "american-flag", "usa"], "mma": ["mma", "ufc", "fighter"],
 "qanon": ["qanon", "q-anon", "qarmy"], "q": ["qanon", "wwg1wga", "qdrop"],
 "potus": ["potus", "president"], "biden": ["biden", "brandon"],
 "trump": ["trump", "maga"], "clinton": ["clinton"], "obama": ["obama"],
 "putin": ["putin", "russia"], "hillary": ["hillary"], "hunter": ["hunter-biden"],
 "fauci": ["fauci"], "fbi": ["fbi"], "cia": ["cia"], "doj": ["doj", "justice-department"],
 "navy": ["navy"], "seals": ["seal", "seals", "navy-seal"],
 "antifa": ["antifa"], "blm": ["blm", "black-lives"],
 "ukraine": ["ukraine", "ukrainian", "zelensky"], "israel": ["israel", "idf"],
 "vatican": ["vatican"], "pope": ["pope", "papal"],
 "celebrity": ["austin-steinbart", "celine", "carmen", "astor", "barr", "kardashian", "oprah"],
 "movies": ["movie", "film", "cinema", "star-wars", "matrix", "aliens-rollercoaster"],
 "tv": ["tv", "series", "episode"],
 "cars": ["car", "mustang", "ferrari", "truck", "drivein", "drive-in"],
 "food": ["food", "pizza", "bread", "burger", "dough"],
 "animals": ["duck", "dog", "cat", "bear", "bird", "horse"],
 "religion": ["church", "bible", "jesus", "god", "prayer", "religion"],
 "historical": ["washington-crossing", "1776", "revolution", "leutze", "historical"],
 "document": ["document", "memo", "letter", "report", "filing"],
 "chart": ["chart", "graph", "stats", "poll"],
 "tweet-screenshot": ["twitter", "tweet", "x-post", "screenshot"],
 "music": ["song", "album", "band", "music"], "sports": ["sport", "game", "team", "coach"],
 "memorial": ["memorial", "funeral", "grave", "died", "death"],
 "conspiracy": ["conspiracy", "coverup", "cover-up", "psyop", "false-flag"],
 "protest": ["protest", "riot", "march"], "police": ["police", "cop", "sheriff"],
 "money": ["money", "dollar", "bank", "fed", "economy"],
 "space": ["nasa", "space", "moon", "mars"],
 "tech": ["tech", "ai", "robot", "computer", "internet"],
 "media": ["cnn", "msnbc", "fox", "news", "media", "journalist"],
}

STOPWORDS = set("""a an the and or of to in on at for with from by is are was were be been this that these those
it its as his her their our your my you we they he she i not no but if then than so very just into over under
about all any can do does did how what when where which who why will would may might shall should must have has
had s t re ve ll d m""".split())

# ---------------------------------------------------------------- helpers
def slug_words(name):
    base = re.sub(r"\.[A-Za-z0-9]+$", "", os.path.basename(name)).replace("%20", " ")
    return [p.lower() for p in re.split(r"[\s_\-.()\[\]]+", base) if p]

def slugify(name, taken):
    s = "-".join(slug_words(name))
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s:
        s = "item"
    base, n = s, 2
    while s in taken:
        s = f"{base}-{n}"; n += 1
    return s

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def colour_family(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hd = h * 360
    if s < 0.12: return "mono"
    if s > 0.55 and v > 0.55 and (hd < 20 or hd > 330 or 40 < hd < 70): return "neon"
    if 60 <= hd <= 170: return "green"
    if 175 <= hd <= 250: return "blue"
    if 250 < hd <= 330: return "cool"
    if hd < 15 or hd > 345: return "red"
    if 15 <= hd < 60: return "earth"
    return "warm"

def bucket_ratio(w, h):
    r = w / max(h, 1)
    if r > 2.2: return "wide"
    if r > 1.12: return "landscape"
    if r >= 0.88: return "square"
    return "portrait"

def orientation(w, h):
    return "landscape" if w > h * 1.05 else ("portrait" if h > w * 1.05 else "square")

def probe_video(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                              "-show_entries", "stream=width,height,duration",
                              "-of", "json", path], capture_output=True, text=True, timeout=20).stdout
        s = json.loads(out)["streams"][0]
        return int(s.get("width") or 0), int(s.get("height") or 0), (float(s.get("duration") or 0) or None)
    except Exception:
        return 0, 0, None

def has_real_transparency(im):
    if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info:
        a = im.convert("RGBA").getchannel("A")
        hist = a.histogram()
        clear = sum(hist[:200])
        return clear > (im.width * im.height) * 0.004
    return False

def flatten(im):
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im if im.mode == "RGB" else im.convert("RGB")

# ---------------------------------------------------------------- derivatives
def still_derivative(src, dst_base):
    """Long edge <= 1600, JPEG q82 -> step down until under the byte budget.
    PNG only when the image genuinely uses transparency. Returns dict."""
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src)
    keep_png = has_real_transparency(im)
    im = im.convert("RGBA") if keep_png else flatten(im)
    im.thumbnail((MAX_STILL, MAX_STILL), Image.LANCZOS)
    if keep_png:
        dst = dst_base + ".png"
        im.save(dst, "PNG", optimize=True)
        if os.path.getsize(dst) > STILL_BUDGET:
            q = im.quantize(colors=256, method=Image.FASTOCTREE)
            q.save(dst, "PNG", optimize=True)
        if os.path.getsize(dst) > STILL_BUDGET and max(im.size) > 1200:
            q = im.copy(); q.thumbnail((1200, 1200), Image.LANCZOS)
            q.quantize(colors=256, method=Image.FASTOCTREE).save(dst, "PNG", optimize=True)
        ext = "png"
    else:
        dst = dst_base + ".jpg"
        for attempt in range(6):
            if attempt == 0:
                frame = im
            elif attempt <= 3:
                frame = im
            else:
                frame = im.copy()
                frame.thumbnail((1200, 1200), Image.LANCZOS)
            buf = dst + ".tmp"
            frame.save(buf, "JPEG", quality=(82, 78, 74, 70, 82, 76)[attempt],
                       optimize=True, progressive=True)
            os.replace(buf, dst)
            if os.path.getsize(dst) <= STILL_BUDGET:
                break
        ext = "jpg"
    w, h = Image.open(dst).size
    im.close()
    return {"path": dst, "ext": ext, "w": w, "h": h}

def gif_derivative(src, dst_base):
    """Animated GIF stays an animated GIF. Max 800 wide, then progressively
    smaller until it fits the byte budget. Falls back to Pillow if ffmpeg fails."""
    dst = dst_base + ".gif"
    try:
        im = Image.open(src)
        w, h = im.size
        frames = getattr(im, "n_frames", 1)
        im.close()
    except Exception:
        w, h, frames = 0, 0, 1
    width = min(w or GIF_MAX_W, GIF_MAX_W)
    ok = False
    for _ in range(8):
        tmp = dst + ".tmp.gif"
        vf = (f"[0:v]scale={width}:-1:flags=lanczos,split[a][b];"
              f"[a]palettegen=max_colors=128:reserve_transparent=1[p];"
              f"[b][p]paletteuse=dither=bayer:bayer_scale=4")
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src,
                            "-filter_complex", vf, "-loop", "0", tmp],
                           capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            try:
                check = Image.open(tmp); nf = getattr(check, "n_frames", 1); check.close()
            except Exception:
                nf = 0
            if nf > 1:
                os.replace(tmp, dst)
                ok = True
                if os.path.getsize(dst) <= GIF_BUDGET:
                    break
        if os.path.exists(tmp):
            os.remove(tmp)
        width = int(width * 0.78)
        if width < 140:
            break
    if not ok:  # Pillow fallback, same rules
        from PIL import ImageSequence
        im = Image.open(src)
        size = (min(im.width, GIF_MAX_W), max(1, round(im.height * min(im.width, GIF_MAX_W) / im.width)))
        out, durs = [], []
        for fr in ImageSequence.Iterator(im):
            durs.append(fr.info.get("duration", im.info.get("duration", 100)))
            out.append(fr.convert("RGBA").resize(size, Image.LANCZOS))
        out[0].save(dst, "GIF", save_all=True, append_images=out[1:], duration=durs,
                    loop=im.info.get("loop", 0), disposal=2, optimize=True)
    w2, h2 = Image.open(dst).size
    return {"path": dst, "ext": "gif", "w": w2, "h": h2}

def video_derivative(src, dst_base):
    """The clip itself is left exactly as it is (copied into memes/web only if it
    is not already there), plus a poster frame so the tile is never blank."""
    ext = src.rsplit(".", 1)[-1].lower()
    dst = dst_base + "." + ext
    if os.path.abspath(src) != os.path.abspath(dst):
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
    poster = dst_base + "-poster.jpg"
    w, h, dur = probe_video(dst)
    ss = "0.6" if (dur or 0) > 1.2 else "0"
    for attempt in (0, 1):
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", ss, "-i", dst,
                            "-frames:v", "1", "-vf", "scale=854:-2", "-q:v", "4", poster],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and os.path.exists(poster) and os.path.getsize(poster) > 0:
            break
        ss = "0"
    else:
        poster = None
    return {"path": dst, "ext": ext, "w": w, "h": h, "duration": dur, "poster": poster}

# ---------------------------------------------------------------- analysis
def ocr_text(path, cache, key):
    if key in cache:
        return cache[key]
    txt = ""
    try:
        from PIL import ImageOps
        os.makedirs(WORK, exist_ok=True)
        tmp = os.path.join(WORK, "_ocr_tmp_intake.png")
        base = Image.open(path).convert("L")
        base.thumbnail((1400, 1400))
        base = ImageOps.autocontrast(base)
        # Tesseract wants dark text on light paper. Try the image both ways and
        # keep whichever read actually found words.
        best = ""
        for variant in (base, ImageOps.invert(base)):
            variant.save(tmp)
            r = subprocess.run(["tesseract", tmp, "stdout", "--psm", "6", "--dpi", "150"],
                               capture_output=True, text=True, timeout=40)
            got = re.sub(r"\s+", " ", r.stdout or "").strip()
            if len(got) > len(best):
                best = got
        txt = best
        if os.path.exists(tmp):
            os.remove(tmp)
    except Exception:
        txt = ""
    keep = " ".join(txt.split(" ")[:40])[:600]
    cache[key] = keep
    return keep

def analyse_image(path):
    """palette / family / brightness / detail / textLikely / size — same
    measurements the page's existing records were built from."""
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(path)
    frames = getattr(im, "n_frames", 1)
    rgb = im.convert("RGB")
    w, h = rgb.size
    small = rgb.copy(); small.thumbnail((160, 160))
    q = small.quantize(colors=8, method=Image.MEDIANCUT).convert("RGB")
    top = [c for c, _ in Counter(q.getdata()).most_common(8)]
    palette = ["#%02x%02x%02x" % c for c in top if not (min(c) > 238 or max(c) < 18)][:3]
    for c in top:
        if len(palette) >= 3: break
        hx = "#%02x%02x%02x" % c
        if hx not in palette: palette.append(hx)
    while len(palette) < 3:
        palette.append(palette[0] if palette else "#000000")
    best = max(top[:5], key=lambda c: (max(c) - min(c)))
    fam = colour_family(best)
    g = small.convert("L"); g.thumbnail((64, 64))
    px = list(g.getdata())
    bright = "dark" if sum(px) / max(len(px), 1) < 78 else ("bright" if sum(px) / max(len(px), 1) > 172 else "mid")
    edges = 0
    gw, gh = g.size
    gd = list(g.getdata())
    for y in range(1, gh):
        row = y * gw
        for x in range(1, gw):
            i = row + x
            if abs(gd[i] - gd[i - 1]) + abs(gd[i] - gd[i - gw]) > 42:
                edges += 1
    density = edges / max(gw * gh, 1)
    detail = "busy" if density > 0.16 else "flat"
    text_likely = bool(density > 0.10 and bright != "dark")
    im.close()
    return {"w": w, "h": h, "frames": frames, "palette": palette, "family": fam,
            "brightness": bright, "detail": detail, "textLikely": text_likely}

# Type tag: Duck's rule -- each meme gets exactly one: meme (still photo), clip
# (video), gif (animated). Derived from the kind the build already worked out.
TYPE_WORDS = {"photo", "video"}

def type_tag(kind, animated=False):
    k = (kind or "").lower()
    if animated or k in ("gif", "animated"):
        return "gif"
    if k in ("video", "mp4", "mov"):
        return "clip"
    return "meme"

def build_topics(src, slug, title, kind, ocr, fam, bright, detail, w, h, animated, duration):
    words = set(slug_words(src)) | set(slug_words(slug)) | set(slug_words(title))
    blob = " ".join([ocr.lower(), title.lower(), src.lower()])
    topics = []
    for tag, keys in ENTITY_TAGS.items():
        for k in keys:
            if k in words or any(k in w2 for w2 in words) or k.replace("-", " ") in blob or k in blob:
                topics.append(tag); break
    for w2 in words:
        if len(w2) > 2 and w2 not in STOPWORDS and not w2.isdigit() and not re.fullmatch(r"\d+x\d+", w2):
            topics.append(w2)
    for tok in re.findall(r"\b[A-Z][A-Za-z]{3,}\b", ocr)[:6]:
        topics.append(tok.lower())
    if kind in ("screenshot", "document") or (detail == "flat" and bright == "bright"):
        topics.append("document")
    if re.search(r"\b(twitter|tweet|@\w+|retweet)\b", ocr.lower()): topics.append("tweet-screenshot")
    if re.search(r"\b(chart|graph|%|poll)\b", ocr.lower()): topics.append("chart")
    topics += [fam, bright, detail, orientation(w, h), bucket_ratio(w, h)]
    if animated: topics.append("animated")
    topics.append(type_tag(kind, animated))
    return sorted({t for t in topics if t and len(t) > 1 and t not in STOPWORDS})

# ---------------------------------------------------------------- enrichment
# Re-derive a rich, deterministic identifier set for records already held.
# Every value below is measured from the file on disk or read from the filename
# / EXIF. Nothing is guessed: a dimension that cannot be measured is left off
# the record rather than filled with a placeholder.

HUE_NAMES = [(15, "crimson"), (40, "orange"), (60, "amber"), (75, "gold"),
             (95, "yellow"), (150, "green"), (175, "teal"), (200, "cyan"),
             (235, "azure"), (260, "blue"), (285, "indigo"), (315, "violet"),
             (340, "magenta"), (360, "crimson")]

SS_NAME = re.compile(r"(screen[\s_-]?shot|screencap|capture|snip|print[\s_-]?screen|"
                     r"tweet|twitter|instagram|facebook|reddit|4chan|8chan|8kun|gab\.|telegram)", re.I)

PHONE_RATIOS = (0.4615, 0.5625, 0.5, 0.75)   # 9:19.5, 9:16, 1:2, 3:4 portrait

def hue_name(hd):
    for lim, name in HUE_NAMES:
        if hd <= lim:
            return name
    return "crimson"

def named_colour(hd, sat, val):
    """Human colour family from hue/sat/value (sat, val 0-1)."""
    if sat < 0.13 or val < 0.06:
        if val < 0.18:  return "ink"
        if val < 0.38:  return "charcoal"
        if val < 0.62:  return "slate"
        if val < 0.80:  return "grey"
        if val < 0.94:  return "silver"
        return "white"
    base = hue_name(hd)
    if val < 0.40:  return "deep " + base
    if val > 0.78:  return "pale " + base
    return base

def temperature_of(hd, sat):
    if sat < 0.13:  return "neutral"
    return "warm" if (hd < 70 or hd > 300) else ("cool" if 150 < hd < 270 else "neutral")

def measure_visual(path):
    """Luma / contrast / saturation / hue / colour family / texture / edge density."""
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(path)
    frames = getattr(im, "n_frames", 1)
    try:
        im.seek(0)
    except Exception:
        pass
    rgb = im.convert("RGB")
    w, h = rgb.size
    t = rgb.copy(); t.thumbnail((128, 128))
    n = t.width * t.height or 1

    g = t.convert("L")
    px = list(g.getdata())
    mean = sum(px) / n
    sd = (sum((v - mean) ** 2 for v in px) / n) ** 0.5

    sp = list(t.convert("HSV").getchannel("S").getdata())
    sat = (sum(sp) / n) / 255.0

    # dominant saturated colour -> hue
    q = t.quantize(colors=8, method=Image.MEDIANCUT).convert("RGB")
    counts = Counter(q.getdata())
    hd, best_sat, best_val, dom = 0.0, 0.0, 0.0, None
    for c, cnt in counts.most_common():
        r_, g_, b_ = [x / 255.0 for x in c]
        h_, s_, v_ = colorsys.rgb_to_hsv(r_, g_, b_)
        if s_ < 0.15 or v_ < 0.08:
            continue
        if s_ * cnt > best_sat:
            best_sat, best_val, hd = s_, v_, h_ * 360
            dom = c
    neutral_hue = best_sat < 0.15
    if dom is None:  # genuinely neutral image
        best_sat, best_val = 0.0, mean / 255.0

    # edge density = texture / detail level
    gg = g.copy(); gg.thumbnail((64, 64))
    gw, gh = gg.size
    gd = list(gg.getdata())
    edges = 0
    for y in range(1, gh):
        row = y * gw
        for x in range(1, gw):
            i = row + x
            if abs(gd[i] - gd[i - 1]) + abs(gd[i] - gd[i - gw]) > 42:
                edges += 1
    density = edges / max(gw * gh, 1)

    dom_hex = "#%02x%02x%02x" % (dom or (int(mean), int(mean), int(mean)))
    out = {
        "width": w, "height": h, "frames": frames,
        "mean_luma": round(mean, 1),
        "brightnessPct": int(round(mean / 255 * 100)),
        "contrast": int(round(min(sd / 127.5, 1) * 100)),
        "saturation": int(round(min(sat, 1) * 100)),
        "texturePct": int(round(min(density / 0.30, 1) * 100)),
        "detailLevel": ("smooth" if density < 0.04 else "soft" if density < 0.10
                        else "textured" if density < 0.18 else "busy"),
        "dominantHex": dom_hex,
        "hue": None if neutral_hue else int(round(hd)) % 360,
        "colourFamily": named_colour(hd, best_sat, max(best_val, mean / 255.0)),
        "temperature": temperature_of(hd, best_sat),
    }
    im.close()
    return out

COMMON_WORDS = set()
_COMMON_PATH = os.path.join(ROOT, "tools/data/words-common.txt")
if os.path.exists(_COMMON_PATH):
    with open(_COMMON_PATH, encoding="utf-8", errors="ignore") as _f:
        COMMON_WORDS = {ln.strip().lower() for ln in _f if len(ln.strip()) > 2}

ENTITY_KEYS = {k for keys in ENTITY_TAGS.values() for k in keys}

def word_shape_ok(w):
    if len(w) < 3 or w in STOPWORDS:
        return False
    if not re.search(r"[aeiouy]", w):
        return False
    if re.search(r"(.)\1\1", w):            # eee, sss
        return False
    if re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", w):
        return False
    return 0.18 <= len(re.findall(r"[aeiouy]", w)) / len(w) <= 0.80

def clean_words(text, cap=24, corpus=None):
    """Distinct words out of OCR noise. A token is kept only when it is a common
    English word, a known entity, or a word that occurs more than once across the
    whole corpus and looks like a word. Fragments are dropped, not guessed at."""
    corpus = corpus or {}
    out, seen = [], set()
    for tok in re.findall(r"[A-Za-z][A-Za-z'\u2019]{2,23}", text or ""):
        w = tok.lower().replace("'", "").replace("\u2019", "")
        if w in seen or not word_shape_ok(w):
            continue
        trusted = (w in COMMON_WORDS or w in ENTITY_KEYS
                   or (len(w) >= 4 and corpus.get(w, 0) >= 2))
        if not trusted:
            continue
        seen.add(w); out.append(w)
        if len(out) >= cap:
            break
    return out

def text_confidence(ocr_text, words):
    """0-100. Weak OCR (a handful of fragments, lots of symbols) scores low."""
    raw = (ocr_text or "").strip()
    if not raw:
        return 0
    n = max(len(raw), 1)
    sym = len(re.findall(r"[^A-Za-z0-9\s]", raw)) / n
    wc = len(words)
    score = min(wc / 12.0, 1.0) * 65 + max(0.0, 1 - min(sym / 0.30, 1.0)) * 30
    if wc >= 6:
        score += 5
    return int(round(max(0, min(100, score))))

def filename_words(name):
    base = re.sub(r"\.[A-Za-z0-9]+$", "", os.path.basename(name))
    base = re.sub(r"([a-z])([A-Z])", r"\1 \2", base)
    out = []
    for p in re.split(r"[\s_\-.()\[\]]+", base):
        p = p.strip().lower()
        if not p or p.isdigit() or p in STOPWORDS:
            continue
        if re.fullmatch(r"[0-9a-f]{8,}", p) or re.fullmatch(r"\d+x\d+", p):
            continue
        if len(p) < 2:
            continue
        out.append(p)
    return out

def size_bucket(w, h):
    long_edge = max(w or 0, h or 0)
    if long_edge < 400:   return "thumb"
    if long_edge < 800:   return "small"
    if long_edge < 1200:  return "medium"
    if long_edge < 1600:  return "large"
    return "xl"

def weight_bucket(nbytes):
    if nbytes < 100_000:   return "light"
    if nbytes < 500_000:   return "medium"
    if nbytes < 2_000_000: return "heavy"
    return "very heavy"

def aspect_bucket(w, h):
    r = (w or 1) / max(h or 1, 1)
    if r > 2.4:   return "ultra-wide"
    if r > 1.6:   return "wide"
    if r > 1.15:  return "landscape"
    if r >= 0.87: return "square"
    if r >= 0.65: return "portrait"
    return "tall"

def detect_screenshot(it, words, conf, w, h):
    signals = []
    if SS_NAME.search(it.get("source", "")):
        signals.append("filename")
    if it.get("kind") == "screenshot":
        signals.append("kind")
    if h and w and h > w:
        r = w / h
        if any(abs(r - p) < 0.025 for p in PHONE_RATIOS):
            signals.append("phone-aspect")
    if (w, h) in ((1366, 768), (1920, 1080), (1440, 900), (1280, 720), (1600, 900)):
        signals.append("desktop-aspect")
    if len(words) >= 6 and conf >= 45:
        signals.append("text-density")
    return (len(signals) >= 2), signals

ENT_ORDER = list(ENTITY_TAGS.keys())

def entity_hits(blob, words):
    hits = []
    for tag in ENT_ORDER:
        for k in ENTITY_TAGS[tag]:
            if k in blob or k in words:
                hits.append(tag)
                break
    return hits

def rich_topics(rec, vis, words, fwords, ents):
    """Compact lowercase slugs built from every identifier we just measured."""
    out, seen = [], set()
    def add(x):
        s = re.sub(r"[^a-z0-9]+", "-", str(x).lower()).strip("-")
        if not s or len(s) < 2 or s in STOPWORDS or s.isdigit() or s in seen:
            return
        if s in TYPE_WORDS:          # bare "photo" / "video" are never topics;
            return                   # the type tag carries that instead
        seen.add(s); out.append(s)
    for e in ents:                       add(e)
    for w in fwords:                     add(w)
    for w in words[:14]:                 add(w)
    add(rec.get("typeTag") or type_tag(rec.get("kind"), rec.get("animated")))
    add(rec.get("motion"))
    add(rec.get("orientation"))
    add(rec.get("aspect"))
    add(rec.get("sizeBucket"))
    add(rec.get("weightBucket"))
    if vis:
        add(vis["colourFamily"])
        add(vis["temperature"])
        if vis.get("hue") is not None:
            add(hue_name(vis["hue"]))
    add(rec.get("family"))
    add(rec.get("brightness"))
    add(rec.get("detail"))
    if rec.get("detailLevel"): add(rec["detailLevel"])
    if rec.get("screenshot"):  add("screenshot")
    if rec.get("textInImage"): add("text-in-image")
    if rec.get("year"):
        add(str(rec["year"])); add(rec.get("decade"))
    if rec.get("animated"):    add("animated")
    return out[:40]

def enrich_all():
    """Re-tag every existing record in place. id / file / source / sha256 / added
    are never touched. Writes memes.json once, atomically."""
    doc = load_data()
    items = doc["items"]
    backup = os.path.join(ROOT, ".qa", "memes-before-enrich.json")
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    if not os.path.exists(backup):
        shutil.copy2(DATA, backup)

    # corpus pass: a word-shaped token seen more than once across the OCR of the
    # whole set is probably real text; a one-off fragment is not trusted.
    corpus = Counter()
    for it in items:
        for tok in re.findall(r"[A-Za-z][A-Za-z'\u2019]{2,23}", it.get("ocr") or ""):
            corpus[tok.lower().replace("'", "").replace("\u2019", "")] += 1

    measured = skipped = 0
    for it in items:
        path = os.path.join(ROOT, it.get("file", ""))
        vis = None
        src_for_pixels = None
        if os.path.exists(path):
            src_for_pixels = path
        elif it.get("poster") and os.path.exists(os.path.join(ROOT, it["poster"])):
            src_for_pixels = os.path.join(ROOT, it["poster"])
        if src_for_pixels and it.get("ext") not in VID_EXT:
            try:
                vis = measure_visual(src_for_pixels); measured += 1
            except Exception as e:
                sys.stderr.write(f"visual fail {it['id']}: {type(e).__name__}: {e}\n")
        elif src_for_pixels:
            try:
                vis = measure_visual(src_for_pixels); measured += 1
            except Exception as e:
                sys.stderr.write(f"poster fail {it['id']}: {e}\n")
        else:
            skipped += 1

        w, h = it.get("width") or 0, it.get("height") or 0
        ocr = it.get("ocr") or ""
        words = clean_words(ocr, corpus=corpus)
        conf = text_confidence(ocr, words)
        fwords = filename_words(it.get("source", ""))

        it["motion"] = ("video" if it.get("kind") == "video" or it.get("ext") in VID_EXT
                        else "animated" if it.get("animated") else "still")
        it["orientation"] = it.get("orientation") or orientation(w, h)
        it["aspect"] = aspect_bucket(w, h)
        it["dimensions"] = f"{w}\u00d7{h}" if w and h else None
        it["sizeBucket"] = size_bucket(w, h)
        it["weightBucket"] = weight_bucket(it.get("bytes") or 0)
        if vis:
            it["colourFamily"] = vis["colourFamily"]
            it["hue"] = vis["hue"]
            it["hueName"] = hue_name(vis["hue"]) if vis["hue"] is not None else None
            it["temperature"] = vis["temperature"]
            it["dominantHex"] = vis["dominantHex"]
            it["brightnessPct"] = vis["brightnessPct"]
            it["contrast"] = vis["contrast"]
            it["saturation"] = vis["saturation"]
            it["texturePct"] = vis["texturePct"]
            it["detailLevel"] = vis["detailLevel"]
        it["textWords"] = words
        it["textWordCount"] = len(words)
        it["textConfidence"] = conf
        it["textInImage"] = bool(len(words) >= 3 and conf >= 35)
        it["filenameWords"] = fwords

        shot, signals = detect_screenshot(it, words, conf, w, h)
        it["screenshot"] = shot
        it["screenshotSignals"] = signals

        # year only where a date genuinely appears in the filename. EXIF is not
        # used: the copies we hold carry only a file-write DateTime, which is the
        # day the file was saved, not the day the picture was made.
        yr, ysrc = None, None
        for cand in re.findall(r"(?<!\d)(1[89]\d{2}|20[0-2]\d)(?!\d)", it.get("source", "")):
            yr, ysrc = int(cand), "filename"
            break

        it["year"] = yr
        it["yearSource"] = ysrc
        it["decade"] = f"{yr // 10 * 10}s" if yr else None

        blob = " ".join([" ".join(fwords), ocr.lower(), (it.get("title") or "").lower(),
                         it.get("source", "").lower()])
        ents = entity_hits(blob, set(fwords) | set(words))
        it["entityTags"] = ents
        it["topics"] = rich_topics(it, vis, words, fwords, ents)

        # faces: stills only; gifs and clips stay null (unknown) on purpose.
        it["faces"] = face_scan(path, it.get("ext")) if os.path.exists(path) else None
        if not isinstance(it.get("people"), list):
            it["people"] = []      # reserved for names Duck confirms; never invented
        it["topics"] = with_face_tags(it["topics"], it["faces"])

    doc["count"] = len(items)
    doc["enriched"] = datetime.date.today().isoformat()
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, DATA)
    print(f"enrich: {len(items)} records, {measured} measured, {skipped} without pixels")
    return len(items), measured, skipped

# ---------------------------------------------------------------- data
def load_data():
    with open(DATA) as f:
        return json.load(f)

def face_cascade():
    """Loaded once per run. False when the cascade file is unusable."""
    global _FACE_CASCADE, _face_warned
    if _FACE_CASCADE is None:
        try:
            import cv2
            c = cv2.CascadeClassifier(FACE_CASCADE_PATH)
            _FACE_CASCADE = False if c.empty() else c
        except Exception as e:
            sys.stderr.write(f"face cascade unavailable: {type(e).__name__}: {e}\n")
            _FACE_CASCADE = False
        if _FACE_CASCADE is False and not _face_warned:
            sys.stderr.write(f"face cascade unusable: {FACE_CASCADE_PATH}\n")
            _face_warned = True
    return _FACE_CASCADE or None

def face_scan(path, ext=None):
    """Count faces in a STILL. Returns {"count": n, "largestPct": pct} where
    largestPct is the biggest box's area as a % of the frame (1 dp), or None
    when the answer is unknown (GIF/video/other format, unreadable file,
    cascade missing). Percentage is scale-invariant, so scanning the 900px
    copy gives the same number as scanning the original."""
    ext = (ext or os.path.splitext(path)[1].lstrip(".")).lower()
    if ext not in FACE_EXT:
        return None
    cas = face_cascade()
    if cas is None:
        return None
    try:
        import cv2
        img = cv2.imread(path)
        if img is None:
            return None
        h, w = img.shape[:2]
        if max(h, w) > FACE_LONG:
            s = FACE_LONG / float(max(h, w))
            img = cv2.resize(img, (max(1, int(round(w * s))), max(1, int(round(h * s)))),
                             interpolation=cv2.INTER_AREA)
        fh, fw = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        boxes = cas.detectMultiScale(gray, FACE_SCALE, FACE_NEIGHBOURS, minSize=(FACE_MIN, FACE_MIN))
        if len(boxes) == 0:
            return {"count": 0, "largestPct": 0.0}
        largest = max(float(bw) * float(bh) for (_x, _y, bw, bh) in boxes)
        return {"count": int(len(boxes)),
                "largestPct": round(largest / (float(fw) * float(fh)) * 100.0, 1)}
    except Exception as e:
        sys.stderr.write(f"face fail {os.path.basename(path)}: {type(e).__name__}: {e}\n")
        return None

def face_tags(n):
    if not n or n < 1:
        return []
    if n == 1:
        return ["face", "one face"]
    if n == 2:
        return ["face", "two faces"]
    return ["face", "crowd"]

def with_face_tags(topics, faces):
    """Merge the face tags into an existing tag list without dropping a tag.
    Only the face tags themselves are refreshed, so a re-run stays idempotent."""
    n = (faces or {}).get("count") if isinstance(faces, dict) else None
    out = [t for t in (topics or []) if t not in FACE_TAGS]
    for t in face_tags(n):
        if t not in out:
            out.append(t)
    return out

# ---- faces pass: re-scan every held record in place ----------------------
def scan_faces():
    """Idempotent maintenance pass: faces / people / face tags on every record.
    id, file, source, sha256, added and every other field are left alone."""
    doc = load_data()
    items = doc["items"]
    changed = unknown = kept_people = 0
    for it in items:
        path = os.path.join(ROOT, it.get("file", ""))
        faces = face_scan(path, it.get("ext")) if os.path.exists(path) else None
        if faces is None:
            unknown += 1
        it["faces"] = faces
        if "people" not in it or not isinstance(it.get("people"), list):
            it["people"] = []
        elif it["people"]:
            kept_people += 1
        merged = with_face_tags(it.get("topics"), faces)
        if merged != it.get("topics"):
            it["topics"] = merged
        changed += 1
    save_data(doc)
    stills = [i for i in items if (i.get("faces") or {}).get("count") is not None]
    n_face = sum(1 for i in stills if i["faces"] and i["faces"]["count"] >= 1)
    total = sum(i["faces"]["count"] for i in stills if i["faces"])
    print(f"faces: {changed} records scanned, {len(stills)} stills, {unknown} unknown (gif/video), "
          f"{n_face} stills with a face, {total} faces, {kept_people} records kept existing people names")
    return changed, unknown

def save_data(doc):
    doc["count"] = len(doc["items"])
    doc["generated"] = datetime.date.today().isoformat()
    tmp = DATA + ".tmp"
    with open(tmp, "w") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, DATA)

# ---------------------------------------------------------------- intake
def intake(folder, no_ocr=False, dry=False, start=0, count=None):
    doc = load_data()
    items = doc["items"]
    by_sha = {it.get("sha256"): it for it in items if it.get("sha256")}
    by_name = {os.path.basename(it.get("source", "")).lower(): it for it in items if it.get("source")}
    taken = {it["id"] for it in items}
    cache = json.load(open(OCR_CACHE)) if os.path.exists(OCR_CACHE) else {}

    added = skipped = failed = 0
    new = []
    pending = []
    unsupported = []
    # Candidate list is fixed and sorted BEFORE any slicing, so --start/--count
    # batches walk a stable order and never overlap or skip a file.
    cands = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in IMG_EXT | VID_EXT:
            unsupported.append(name)
            continue
        cands.append(name)
    window = cands if count is None else cands[start:start + count]
    for name in window:
        path = os.path.join(folder, name)
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        try:
            digest = sha256(path)
        except Exception as e:
            sys.stderr.write(f"skip {name}: {e}\n"); failed += 1; continue
        if digest in by_sha or name.lower() in by_name:
            skipped += 1
            sys.stderr.write(f"skip-known {name}\n")
            continue
        if dry:
            pending.append(name)
            new.append({"source": name})
            continue

        try:
            sid = slugify(name, taken)
            taken.add(sid)
            base = os.path.join(WEB, sid)
            os.makedirs(WEB, exist_ok=True)

            # 1. park the original in staging (never overwrite an existing file)
            original = os.path.join(STAGING, name)
            if os.path.abspath(os.path.dirname(path)) != os.path.abspath(STAGING):
                os.makedirs(STAGING, exist_ok=True)
                if os.path.exists(original):
                    original = os.path.join(STAGING, f"{sid}-{digest[:8]}.{ext}")
                shutil.copy2(path, original)

            # 2. derivative
            if ext in VID_EXT:
                d = video_derivative(path if os.path.abspath(path) != os.path.abspath(original) else original, base)
            elif ext == "gif":
                d = gif_derivative(original, base)
            else:
                d = still_derivative(original, base)

            # 3. measurements + tags
            if ext in VID_EXT:
                w, h = d["w"], d["h"]
                pal, fam, bright, detail, text_likely = [], "mono", "mid", "flat", False
                animated, duration = False, d.get("duration")
            else:
                a = analyse_image(d["path"])
                w, h = a["w"], a["h"]
                pal, fam, bright, detail, text_likely = a["palette"], a["family"], a["brightness"], a["detail"], a["textLikely"]
                animated = bool(ext == "gif" and a["frames"] > 1)
                duration = round(a["frames"] / 12.0, 2) if animated else None

            kind = ("video" if ext in VID_EXT else
                    "gif" if animated else
                    "screenshot" if (text_likely and detail == "flat" and bright == "bright") else
                    "illustration" if (detail == "flat" and len(set(pal)) <= 2) else
                    "photo")
            if ext == "gif" and animated:
                kind = "gif"

            text = ""
            if not no_ocr and ext in STILL_EXT - {"gif"}:
                text = ocr_text(d["path"], cache, digest)

            title = re.sub(r"\s+", " ", re.sub(r"\.[A-Za-z0-9]+$", "", name).replace("_", " ").replace("-", " ")).strip()
            title = title[:90] or sid
            faces = face_scan(d["path"], d["ext"])
            topics = build_topics(name, sid, title, kind, text, fam, bright, detail, w, h, animated, duration)
            topics = with_face_tags(topics, faces)
            years = re.findall(r"\b(1[89]\d{2}|20[0-2]\d)\b", name + " " + text)
            rec = {
                "id": sid,
                "file": os.path.relpath(d["path"], ROOT).replace(os.sep, "/"),
                "original": os.path.relpath(original, ROOT).replace(os.sep, "/"),
                "title": title,
                "source": name,
                "kind": kind,
                "typeTag": type_tag(kind, animated),
                "ext": d["ext"],
                "bytes": os.path.getsize(d["path"]),
                "width": w, "height": h,
                "ratio": bucket_ratio(w, h),
                "orientation": orientation(w, h),
                "animated": animated,
                "duration_s": round(duration, 2) if duration else None,
                "palette": pal,
                "family": fam,
                "brightness": bright,
                "detail": detail,
                "textLikely": text_likely,
                "topics": topics,
                "faces": faces,
                "people": [],
                "year": int(sorted(years)[0]) if years else None,
                "sha256": digest,
                "added": datetime.date.today().isoformat(),
                "ocr": text,
            }
            if d.get("poster"):
                rec["poster"] = os.path.relpath(d["poster"], ROOT).replace(os.sep, "/")
            new.append(rec)
            by_sha[digest] = rec
            by_name[name.lower()] = rec
            added += 1
        except Exception as e:
            failed += 1
            sys.stderr.write(f"fail {name}: {type(e).__name__}: {e}\n")

    if new and not dry:
        items.extend(new)
        save_data(doc)
        json.dump(cache, open(OCR_CACHE, "w"), ensure_ascii=False)
    total = len(items) if not dry else len(items) + len(new)
    scope = (f"files {start}..{min(start + len(window), len(cands)) - 1} of {len(cands)}"
             if count is not None else f"all {len(cands)} files")
    if dry:
        print(f"memes-intake DRY: {len(pending)} pending, {skipped} already held, "
              f"{failed} unreadable, {len(unsupported)} unsupported-ext ({scope}); "
              f"{len(cands)} holdable files in folder; memes.json holds {len(items)}")
        for n in pending:
            print(f"  pending {n}")
        for n in unsupported:
            print(f"  unsupported {n}")
        return len(pending), skipped, failed
    print(f"memes-intake: {len(new)} added, {skipped} skipped (already held), "
          f"{failed} failed ({scope}) — memes.json now {total} items")
    return len(new), skipped, failed

# ---------------------------------------------------------------- rebuild
def rebuild(start, count):
    """Re-derive memes/web/ for records already in the JSON, against the current
    web-size targets. Originals stay exactly where they are."""
    doc = load_data()
    items = doc["items"][start:start + count]
    done = 0
    for it in items:
        src = os.path.join(ROOT, it.get("original") or os.path.join("memes/staging", it["source"]))
        if not os.path.exists(src):
            sys.stderr.write(f"missing original {it['id']}: {src}\n"); continue
        base = os.path.join(WEB, it["id"])
        ext = it["ext"]
        try:
            if ext in VID_EXT:
                d = video_derivative(src, base)
                if d.get("poster"):
                    it["poster"] = os.path.relpath(d["poster"], ROOT)
            elif ext == "gif":
                d = gif_derivative(src, base)
            else:
                d = still_derivative(src, base)
            it["file"] = os.path.relpath(d["path"], ROOT).replace(os.sep, "/")
            it["original"] = os.path.relpath(src, ROOT).replace(os.sep, "/")
            it["ext"] = d["ext"]
            it["bytes"] = os.path.getsize(d["path"])
            it["width"], it["height"] = d["w"], d["h"]
            it["ratio"] = bucket_ratio(d["w"], d["h"])
            it["orientation"] = orientation(d["w"], d["h"])
            done += 1
        except Exception as e:
            sys.stderr.write(f"fail {it['id']}: {type(e).__name__}: {e}\n")
        save_data(doc)
    total = sum(os.path.getsize(os.path.join(ROOT, i["file"])) for i in doc["items"] if os.path.exists(os.path.join(ROOT, i["file"])))
    print(f"rebuild {start}..{start+len(items)-1}: {done} done | web now {total/1048576:.1f} MB")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Take a folder of meme media into the dump.")
    ap.add_argument("folder", nargs="?", help="folder to intake")
    ap.add_argument("--no-ocr", action="store_true", help="skip OCR for this run")
    ap.add_argument("--dry-run", action="store_true", help="report what would be added, write nothing")
    ap.add_argument("--rebuild", action="store_true", help="maintenance: re-derive memes/web for existing records")
    ap.add_argument("--enrich", action="store_true", help="re-tag every existing record in place (measurements only, ids untouched)")
    ap.add_argument("--faces", action="store_true", help="re-scan held records for faces; writes faces / people / face tags only, ids untouched")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=10**6)
    a = ap.parse_args()
    if a.enrich:
        enrich_all()
    elif a.faces:
        scan_faces()
    elif a.rebuild:
        rebuild(a.start, a.count)
    elif a.folder:
        intake(a.folder, a.no_ocr, a.dry_run,
               a.start, None if a.count == 10**6 else a.count)
    else:
        ap.print_help(); sys.exit(2)
