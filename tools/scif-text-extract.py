#!/usr/bin/env python3
"""Extract the text of every SCI[F] PDF into a cache folder, page by page (input for tools/scif-fulltext-build.py).

  python3 tools/scif-text-extract.py --out /workspace/scif-text-cache [--pdfs DIR] [--only TRD-0033,TRD-0034]

* The PDFs live on R2 (memes.therubberduck.net / media.therubberduck.net); they are downloaded to --pdfs (default: <out>/pdfs).
* Native text comes from the PDF text layer (PyMuPDF). A page is OCR'd with tesseract when that layer is missing,
  short (under 150 characters, with or without an image), or long but junk (font garbage or a rotated scan).
  A layer of 150 characters or more is not trusted just because it is long.
* OCR output that does not look like English (rotated scans) is retried at 90/180/270 degrees and the best reading is kept.
* Output: <out>/<TRD-id>.json = {"id","pages":[page text ...],"ocr":[page numbers that were OCR'd]}.
Needs: pip install pymupdf; apt install tesseract-ocr. Re-runnable: finished documents are skipped.
"""
import argparse, json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
from multiprocessing import Pool
import fitz
fitz.TOOLS.mupdf_display_errors(False)
os.environ['OMP_THREAD_LIMIT'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set('the and of to in that is for with as was on are by this from or be it at an which not have had but his were their has been they its who one all can more also will would there these other than into any may such only when what them out our most those about'.split())
TOK = re.compile(r'[a-z]{2,}')

def english_ratio(t):
    w = TOK.findall(t.lower())
    return (sum(1 for x in w if x in STOP) / len(w)) if len(w) >= 12 else 0.0

def ocr_page(page, rot=0):
    pix = page.get_pixmap(dpi=170, colorspace=fitz.csGRAY, matrix=fitz.Matrix(170 / 72, 170 / 72).prerotate(rot))
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        pix.save(f.name); fn = f.name
    try:
        return subprocess.run(['tesseract', fn, 'stdout', '-l', 'eng', '--psm', '3'], capture_output=True, text=True, timeout=180).stdout
    finally:
        os.unlink(fn)

def needs_ocr(text):
    """True when the text layer should not be trusted and the page image should be read."""
    s = (text or '').strip()
    n = len(s)
    if n < 150:
        return True
    if '(cid:' in s.lower():
        return True
    words = re.findall(r'[A-Za-z]{4,}', s)
    if len(words) >= 20:
        bare = sum(1 for w in words if not re.search(r'[aeiouAEIOU]', w))
        if bare / len(words) >= 0.45:
            return True
    return False

def best_ocr(page):
    t = ocr_page(page)
    if len(TOK.findall(t.lower())) >= 15 and english_ratio(t) < 0.12:
        for rot in (90, 180, 270):
            t2 = ocr_page(page, rot)
            if english_ratio(t2) > english_ratio(t) + 0.05:
                t = t2
    return t

def work(a):
    d, pdf, out = a
    dst = os.path.join(out, d['id'] + '.json')
    if os.path.exists(dst):
        return d['id'], 'skip'
    try:
        doc = fitz.open(pdf)
    except Exception as e:
        json.dump({'id': d['id'], 'pages': [], 'ocr': [], 'error': str(e)[:120]}, open(dst, 'w'))
        return d['id'], 'unreadable'
    pages, ocr = [], []
    for pn, p in enumerate(doc):
        try: t = p.get_text('text')
        except Exception: t = ''
        if needs_ocr(t):
            n = len(t.strip())
            try: o = best_ocr(p)
            except Exception: o = ''
            # keep a real header line and add the reading of the scan
            t = (t + '\n' + o) if n >= 25 else o
            ocr.append(pn + 1)
        pages.append(t)
    json.dump({'id': d['id'], 'pages': pages, 'ocr': ocr}, open(dst, 'w'), ensure_ascii=False)
    return d['id'], 'ok'

def fetch(d, pdfdir):
    f = d['file']
    url = f if re.match(r'https?://', f) else 'https://memes.therubberduck.net/' + '/'.join(urllib.parse.quote(urllib.parse.unquote(s)) for s in f.split('/'))
    dst = os.path.join(pdfdir, d['id'] + '.pdf')
    if not os.path.exists(dst) or os.path.getsize(dst) < 1000:
        req = urllib.request.Request(url, headers={'User-Agent': 'therubberduck-preview'})
        with urllib.request.urlopen(req, timeout=300) as r, open(dst, 'wb') as out:
            while True:
                chunk = r.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
    return dst

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--pdfs'); ap.add_argument('--only'); ap.add_argument('--procs', type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); pdfdir = a.pdfs or os.path.join(a.out, 'pdfs'); os.makedirs(pdfdir, exist_ok=True)
    h = open(os.path.join(ROOT, 'pdfs.html'), encoding='utf-8').read()
    docs = json.loads(re.search(r'var DOCS = (\[.*?\]);\n', h, re.S).group(1))
    if a.only: docs = [d for d in docs if d['id'] in a.only.split(',')]
    jobs = [(d, fetch(d, pdfdir), a.out) for d in docs]
    with Pool(a.procs) as P:
        for i, st in P.imap_unordered(work, jobs):
            print(i, st, flush=True)
