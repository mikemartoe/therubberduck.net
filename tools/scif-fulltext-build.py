#!/usr/bin/env python3
"""Build the SCI[F] full-text search from the text cache made by tools/scif-text-extract.py.

  python3 tools/scif-fulltext-build.py --cache /workspace/scif-text-cache

Writes (all static JSON, lazy-loaded by /assets/trd/scif-search.js):
  scif/text/<TRD-id>.json          page-level text, one file per document: {"id","title","shelf","pages":N,"text":["page 1 text", ...]}
                                   long documents are split: <id>.json is then {"id","title","shelf","pages":N,"per":P,"parts":K}
                                   and <id>.<k>.json (k=0..K-1) holds {"id","from":first page,"text":[...P pages...]}
  scif/search/manifest.json        {"v","docs":[[id,title,shelf,pages,per,kw] ...],"split":[prefixes that use 4 letters],"terms":N}
  scif/search/<ab>.json            inverted index shard for words starting with ab (longer prefix when split): {"word":"doc:p,p,p;doc:p,p"}  (doc = index in manifest.docs, p = 1-based page)
Reusable format for other tools (AI/semantic search): the per-document text JSON above is the canonical page-level text.
Wikipedia is never named on the site (standing rule), so the word and wikipedia URLs are dropped from the indexed text.
"""
import argparse, collections, json, os, re, shutil, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PART_CHARS = 180000      # target characters of text per part file
SHARD_MAX = 150000       # shards are 2 letters; one above this many bytes is split by one more letter
MAX_PAGES_PER_TERM = 7000  # words on more pages than this are stop words and are not indexed
TOKEN = re.compile(r"[a-z0-9]{3,30}|[0-9]{2}")

def clean(t):
    t = t.replace('\x00', ' ')
    t = re.sub(r'(?<=[A-Za-z])-\n(?=[a-z])', '', t)
    t = re.sub(r'https?://\S*wikipedia\.org\S*', ' ', t, flags=re.I)
    t = re.sub(r'wikipedia(?:,? the free encyclopedia)?', '', t, flags=re.I)   # the site never names that source
    t = re.sub(r'[\u0000-\u0008\u000b-\u001f\u007f]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def fold(s):
    s = unicodedata.normalize('NFKD', s.lower())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('\u2019', "'").replace('\u2018', "'")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cache', required=True); a = ap.parse_args()
    h = open('pdfs.html', encoding='utf-8').read()
    docs = json.loads(re.search(r'var DOCS = (\[.*?\]);\n', h, re.S).group(1))
    for d in ('scif/text', 'scif/search'):
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    manifest = []; postings = collections.defaultdict(lambda: collections.defaultdict(list)); chars = 0; pages_total = 0
    for di, d in enumerate(docs):
        src = os.path.join(a.cache, d['id'] + '.json')
        pages = [clean(t) for t in (json.load(open(src, encoding='utf-8')).get('pages') or [])] if os.path.exists(src) else []
        total = sum(len(t) for t in pages); chars += total; pages_total += len(pages)
        per = 0
        meta = {'id': d['id'], 'title': d['title'], 'shelf': d['topic']}
        if total > PART_CHARS * 1.3 and len(pages) > 1:
            per = max(1, int(PART_CHARS / max(1, total / len(pages))))
            parts = (len(pages) + per - 1) // per
            json.dump(dict(meta, pages=len(pages), per=per, parts=parts), open('scif/text/%s.json' % d['id'], 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            for k in range(parts):
                json.dump({'id': d['id'], 'from': k * per + 1, 'text': pages[k * per:(k + 1) * per]}, open('scif/text/%s.%d.json' % (d['id'], k), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(dict(meta, pages=len(pages), text=pages), open('scif/text/%s.json' % d['id'], 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        manifest.append([d['id'], d['title'], d['topic'], len(pages), per, d.get('kw', '')])
        for pn, t in enumerate(pages, 1):
            for w in set(TOKEN.findall(fold(t))):
                postings[w][di].append(pn)
    # drop stop words (words on very many pages)
    drop = [w for w, dd in postings.items() if sum(len(v) for v in dd.values()) > MAX_PAGES_PER_TERM]
    for w in drop: del postings[w]
    enc = {w: ';'.join('%d:%s' % (di, ','.join(map(str, pg))) for di, pg in sorted(dd.items())) for w, dd in postings.items()}
    def pre(w, n): return (w + '_' * n)[:n]
    shards = collections.defaultdict(dict)
    for w, v in enc.items(): shards[pre(w, 2)][w] = v
    split = set()
    while True:                       # a shard over SHARD_MAX bytes is split by one more letter (client follows the 'split' list)
        big = [p for p, dct in shards.items() if len(json.dumps(dct, separators=(',', ':'))) > SHARD_MAX and len(p) < 5]
        if not big: break
        for p in big:
            dct = shards.pop(p); split.add(p)
            for w, v in dct.items(): shards[pre(w, len(p) + 1)][w] = v
    for p, dct in shards.items():
        json.dump(dct, open('scif/search/%s.json' % p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'v': 1, 'built': __import__('datetime').date.today().isoformat(), 'docs': manifest, 'split': sorted(split), 'shards': sorted(shards), 'terms': len(enc), 'stop': sorted(drop)},
              open('scif/search/manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # stamp the build into the engine so browsers and the CDN never serve a mix of old and new files
    import hashlib
    ver = hashlib.sha256(open('scif/search/manifest.json', 'rb').read()).hexdigest()[:10]
    js = open('assets/trd/scif-search.js', encoding='utf-8').read()
    js = re.sub(r"var V = '[^']*';", "var V = '%s';" % ver, js, count=1)
    open('assets/trd/scif-search.js', 'w', encoding='utf-8').write(js)
    jv = hashlib.sha256(open('assets/trd/scif-search.js', 'rb').read()).hexdigest()[:10]
    h2 = open('pdfs.html', encoding='utf-8').read()
    h2 = re.sub(r'/assets/trd/scif-search\.js\?v=[a-z0-9]+', '/assets/trd/scif-search.js?v=' + jv, h2)
    open('pdfs.html', 'w', encoding='utf-8').write(h2)
    # header search (assets/trd/sitenav.js) loads the same engine: point it at this build, then re-stamp sitenav.js on every page that loads it
    sj = open('assets/trd/sitenav.js', encoding='utf-8').read()
    sj = re.sub(r"/assets/trd/scif-search\.js\?v=[a-z0-9]+", '/assets/trd/scif-search.js?v=' + jv, sj)
    open('assets/trd/sitenav.js', 'w', encoding='utf-8').write(sj)
    new = hashlib.sha256(sj.encode('utf-8')).hexdigest()[:10]
    import subprocess
    cur = subprocess.run(['git', 'grep', '-ho', r'sitenav\.js?v=[0-9a-f]\{10\}'], capture_output=True, text=True).stdout.split()
    olds = {c.split('=')[1] for c in cur} - {new}
    for old in olds:
        for f in subprocess.run(['git', 'grep', '-l', 'sitenav.js?v=' + old], capture_output=True, text=True).stdout.split():
            t = open(f, encoding='utf-8').read(); open(f, 'w', encoding='utf-8').write(t.replace('sitenav.js?v=' + old, 'sitenav.js?v=' + new))
    print('sitenav.js?v=%s (replaced %s)' % (new, ', '.join(sorted(olds)) or 'nothing'))
    sz = lambda d: sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)) / 1e6
    print('docs %d, pages %d, text %.1f MB chars; text files %d (%.1f MB); search shards %d (%.1f MB); terms %d; stop words dropped %d; split prefixes %d' % (
        len(docs), pages_total, chars / 1e6, len(os.listdir('scif/text')), sz('scif/text'), len(os.listdir('scif/search')), sz('scif/search'), len(enc), len(drop), len(split)))

if __name__ == '__main__':
    main()
