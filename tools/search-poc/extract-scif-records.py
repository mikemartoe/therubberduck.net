#!/usr/bin/env python3
"""Search proof of concept, SCIF room: turn per-page PDF text into search records.

Reads (never writes) the SCIF retitle worker's page-level text
(JSON per doc: {"n", "pages": [...]}, plus OCR text for scanned pages) and the
catalog numbers on /library/*/index.html. Writes one JSONL row per PDF page:
{id, title, shelf, url, pdf, page, text}. Run from the repo root.
"""
import glob, html, json, os, re, sys
SRC = os.environ.get('SCIF_TEXT', '/workspace/trd-reports/scif-labels-2026-11-28')
OUT = sys.argv[1] if len(sys.argv) > 1 else '/workspace/search-poc-work/scif-pages.jsonl'
cat = {}
for f in glob.glob('library/*/index.html'):
    s = open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'Catalog no\.</dt><dd>(TRD-\d+)', s)
    if not m: continue
    t = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S) or re.search(r'<title>(.*?)</title>', s, re.S)
    sh = re.search(r'<dt>Topic</dt><dd>(.*?)</dd>', s)
    pdf = re.search(r'"contentUrl":"([^"]+\.pdf)"', s)
    clean = lambda x: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', x))).strip()
    cat[m.group(1)] = dict(id=m.group(1), title=clean(t.group(1)) if t else m.group(1),
                           shelf=clean(sh.group(1)) if sh else '', url='/' + os.path.dirname(f) + '/',
                           pdf=pdf.group(1) if pdf else '')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
n = pages = ocr = 0
with open(OUT, 'w', encoding='utf-8') as fh:
    for p in sorted(glob.glob(SRC + '/pages/TRD-*.json')):
        i = os.path.basename(p)[:-5]
        d = json.load(open(p, encoding='utf-8'))
        if 'pages' not in d or i not in cat: continue
        n += 1
        for k, t in enumerate(d['pages']):
            o = f'{SRC}/ocr/{i}_{k}.txt'
            if len(t.strip()) < 25 and os.path.exists(o):
                t = open(o, encoding='utf-8', errors='replace').read(); ocr += 1
            t = re.sub(r'[ \t\r\f\v\u2028\u2029\x00\x85]+', ' ', t).strip()
            if len(t) < 25: continue
            pages += 1
            fh.write(json.dumps(dict(cat[i], page=k + 1, text=t), ensure_ascii=False) + '\n')
print(n, 'docs,', pages, 'pages with text,', ocr, 'from OCR ->', OUT)
