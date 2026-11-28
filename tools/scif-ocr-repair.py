#!/usr/bin/env python3
"""Re-read SCI[F] pages whose published text is too thin or junk.

Reads the live text at --base (the versioned R2 folder), downloads the public PDFs,
and OCRs only the pages tools/scif-text-extract.py would now send to tesseract.
Writes one cache file per repaired document, in the extract format
{"id","pages":[...],"ocr":[page numbers read again]}.

TRD-0087 is never fetched. TRD-0129 is a saved 404 and is not repaired or indexed.
Nothing here is uploaded.

  python3 tools/scif-ocr-repair.py --out /workspace/scif-ocr-repair
"""
import argparse, importlib.util, json, os, sys, urllib.request
from multiprocessing import Pool
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('scif_text_extract', os.path.join(_here, 'scif-text-extract.py'))
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://scif-search.therubberduck.net/scif-search/2beb375c5b/'
UA = {'User-Agent': 'therubberduck-preview'}
SKIP = {'TRD-0087', 'TRD-0129'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)

def pages_of(doc_id, meta, base):
    if 'text' in meta:
        return list(meta['text'])
    out = []
    for k in range(meta.get('parts') or 0):
        part = get(base + 'text/%s.%d.json' % (doc_id, k))
        out.extend(part.get('text') or [])
    return out

def repair_one(job):
    doc_id, pages, bad, d, out, pdfdir = job
    try:
        pdf = ex.fetch(d, pdfdir)
        import fitz
        doc = fitz.open(pdf)
        ocr_pages = []
        for i in bad:
            if i >= doc.page_count:
                continue
            try:
                fresh = ex.best_ocr(doc[i])
            except Exception:
                fresh = ''
            old = pages[i] or ''
            if len(old.strip()) >= 25 and len(fresh.strip()) < 40:
                continue
            pages[i] = fresh if len(old.strip()) < 25 else (old + '\n' + fresh)
            ocr_pages.append(i + 1)
        doc.close()
        json.dump({'id': doc_id, 'pages': pages, 'ocr': ocr_pages}, open(os.path.join(out, doc_id + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        return doc_id, len(ocr_pages), len(bad), ''
    except Exception as e:
        return doc_id, 0, len(bad), repr(e)[:240]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='/workspace/scif-ocr-repair')
    ap.add_argument('--base', default=BASE)
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()
    base = a.base if a.base.endswith('/') else a.base + '/'
    os.makedirs(a.out, exist_ok=True)
    pdfdir = os.path.join(a.out, 'pdfs')
    os.makedirs(pdfdir, exist_ok=True)
    man = get(base + 'search/manifest.json')
    html = open(os.path.join(ROOT, 'pdfs.html'), encoding='utf-8').read()
    import re
    docs = {d['id']: d for d in json.loads(re.search(r'var DOCS = (\[.*?\]);\n', html, re.S).group(1))}
    jobs = []
    flagged = []
    for row in man['docs']:
        doc_id = row[0]
        if doc_id == 'TRD-0129':
            flagged.append(doc_id)
            continue
        if doc_id in SKIP or doc_id not in docs:
            continue
        meta = get(base + 'text/' + doc_id + '.json')
        pages = pages_of(doc_id, meta, base)
        bad = []
        for i, t in enumerate(pages):
            n = len((t or '').strip())
            # The published short pages (under 25 everywhere, under 150 in TRD-0242)
            # plus a long layer that is font garbage or a rotated scan.
            if n < 25 or (doc_id == 'TRD-0242' and n < 150) or (n >= 150 and ex.needs_ocr(t or '')):
                bad.append(i)
        if not bad:
            continue
        jobs.append((doc_id, pages, bad, docs[doc_id]))
    thin = sum(1 for _, pages, bad, _ in jobs for i in bad if len((pages[i] or '').strip()) < 150)
    print('documents %d, pages to read %d, of which under 150 characters %d' % (len(jobs), sum(len(b) for _, _, b, _ in jobs), thin), flush=True)
    print('flagged, not read:', ', '.join(flagged) or 'none', flush=True)

    done = 0
    packed = [job + (a.out, pdfdir) for job in jobs]
    with Pool(a.procs) as pool:
        for doc_id, n, asked, err in pool.imap_unordered(repair_one, packed):
            done += 1
            print('%s re-read %d/%d (%d/%d documents)%s' % (doc_id, n, asked, done, len(jobs), (' ERROR ' + err) if err else ''), flush=True)
    note = os.path.join(a.out, 'README.txt')
    open(note, 'w', encoding='utf-8').write(
        'Repaired SCI[F] page text. Same shape as tools/scif-text-extract.py '
        '(id, pages, ocr). Not uploaded. TRD-0129 was not read: it is a saved 404.\n')
    print('wrote', a.out, flush=True)

if __name__ == '__main__':
    main()
