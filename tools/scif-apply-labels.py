#!/usr/bin/env python3
"""Apply tools/scif-labels.json (id -> title, desc, topic, kw) to the SCI[F] room data.

Source of truth for document names is tools/scif-labels.json. This script:
  * rewrites title / desc / topic / kw in the DOCS array inside pdfs.html (TRD-#### ids, file names, pages are untouched)
  * refreshes tools/library-names.json so /library/<slug>/ pages use the same title and description
Library URLs stay stable because tools/library-slugs.json freezes each id's slug.
Run from the repo root, then:  python3 tools/seo-build.py --only library && python3 tools/site-search-build.py
Rollback: git checkout the previous pdfs.html / tools/library-names.json and re-run the two builds.
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
labels = json.load(open('tools/scif-labels.json', encoding='utf-8'))
html = open('pdfs.html', encoding='utf-8').read()
m = re.search(r'var DOCS = (\[.*?\]);\n', html, re.S)
docs = json.loads(m.group(1))
changed = 0
retitled = set()
for d in docs:
    lb = labels.get(d['id'])
    if not lb:
        continue
    new = dict(d)
    new['title'], new['desc'], new['topic'] = lb['title'], lb['desc'], lb['topic']
    if lb.get('kw'):
        new['kw'] = lb['kw']
    if new != d:
        changed += 1
        if (new['title'], new['desc']) != (d['title'], d['desc']):
            retitled.add(d['id'])
    # keep key order stable: put kw right after topic
    order = ['id', 'file', 'name', 'title', 'level', 'desc', 'topic', 'kw', 'pages', 'bytes', 'mb', 'thumb', 'large']
    d.clear(); d.update({k: new[k] for k in order if k in new}); d.update({k: v for k, v in new.items() if k not in d})
out = json.dumps(docs, separators=(',', ':'))
html = html[:m.start(1)] + out + html[m.end(1):]
open('pdfs.html', 'w', encoding='utf-8').write(html)
names = json.load(open('tools/library-names.json', encoding='utf-8'))
for i, lb in labels.items():
    prev = names.get(i)
    if prev is None and i not in retitled:
        continue
    prev = prev or {}
    # library pages keep their existing long-form text (about) when there is one; titles always follow the labels
    names[i] = {'title': lb['title'], 'about': prev.get('about') or lb['desc'], 'source': prev.get('source') or 'SCI[F] label pass 2026-11-28: read from the PDF (page 1 text, metadata or OCR)'}
json.dump(names, open('tools/library-names.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('DOCS updated:', changed, 'of', len(docs), '; names:', len(names))
