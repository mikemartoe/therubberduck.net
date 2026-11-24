#!/usr/bin/env python3
"""Apply the reusable 'support the mission' block to every DUCK SAUCE article.

  python3 tools/newsroom-support.py         # write
  python3 tools/newsroom-support.py --dry   # report only

Run automatically from tools/newsroom-feeds.py on each publish so new
stories get the block. Existing source text is not touched. The block is
inserted after the story (and its photos) and immediately before the
share section. Idempotent: a previous block is replaced in place.
"""
from __future__ import annotations
import argparse, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'tools', 'templates', 'article-support.html')
CSS_HREF_RE = re.compile(r'(href="/assets/trd/newsroom\.css\?v=)[^"]+"')
CSS_VER = 'ducksauce7'
# Whole previous block, including a leading newline if we inserted one.
BLOCK_RE = re.compile(
    r'\n?<aside class="ds-support"[^>]*>.*?</aside>\n?',
    re.S,
)
SHARE_RE = re.compile(r'<section class="dx-share"')
AFTER_RE = re.compile(r'<p class="after">')
ARTICLE_END_RE = re.compile(r'</article>')


def load_block():
    raw = open(TEMPLATE, encoding='utf-8').read()
    # Keep only the aside; drop the HTML comment header so pages stay tight.
    m = re.search(r'<aside class="ds-support".*</aside>', raw, re.S)
    if not m:
        raise SystemExit('tools/templates/article-support.html is missing the aside')
    return m.group(0).strip()


def insert(html, block):
    html = BLOCK_RE.sub('', html)
    payload = '\n' + block + '\n'
    if SHARE_RE.search(html):
        return SHARE_RE.sub(payload + '<section class="dx-share"', html, count=1), 'before-share'
    if AFTER_RE.search(html):
        return AFTER_RE.sub(payload + '<p class="after">', html, count=1), 'before-after'
    if ARTICLE_END_RE.search(html):
        return ARTICLE_END_RE.sub(payload + '</article>', html, count=1), 'before-article-end'
    return html, None


def bump_css(html):
    if not CSS_HREF_RE.search(html):
        return html, False
    new, n = CSS_HREF_RE.subn(rf'\1{CSS_VER}"', html, count=1)
    return new, n > 0 and new != html


def articles():
    return sorted(glob.glob(os.path.join(ROOT, 'newsroom', '*', 'index.html')))


def apply(dry=False):
    block = load_block()
    rows = []
    for path in articles():
        original = open(path, encoding='utf-8').read()
        html, where = insert(original, block)
        html, css = bump_css(html)
        slug = os.path.basename(os.path.dirname(path))
        changed = html != original
        rows.append((slug, where, css, changed))
        if changed and not dry:
            open(path, 'w', encoding='utf-8').write(html)
    return rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    rows = apply(dry=a.dry)
    missing = [s for s, w, _, _ in rows if not w]
    if missing:
        print('no insertion point:', ', '.join(missing), file=sys.stderr)
        sys.exit(1)
    changed = sum(1 for *_, c in rows if c)
    print(f'{"dry run, would update" if a.dry else "updated"} {changed} of {len(rows)} articles '
          f'(css ?v={CSS_VER})')
    for slug, where, css, changed in rows:
        print(f'  {slug}: {where}{"  css-bust" if css else ""}{"  written" if changed and not a.dry else ""}')
