#!/usr/bin/env python3
"""Mike's rule (Oct 27 2026): Wikipedia is never named, linked or used as a source on therubberduck.net.
- Wikipedia links inside archived Q drops / X posts -> plain "(ref: Topic)" (no link, no name).
- Library/PDF display titles: drop "Wikipedia" / "Wikipedia, the free encyclopedia" (PDF files, thumbs and page URLs untouched).
Re-runnable; prints per-file counts. Usage: python3 tools/strip_wikipedia.py [--apply]"""
import re,sys,subprocess,urllib.parse,html
APPLY='--apply' in sys.argv
W=r'https?://\s?(?:[a-z]{2}\.)?(?:m\.)?wikipedia\.org/wiki/([^\s"<>\\)\]]+)'
def topic(m):
    t=m.group(1).split('#')[0]
    t=html.unescape(urllib.parse.unquote(t)).replace('_',' ').strip()
    return '(ref: '+html.escape(t,quote=False)+')'
A=re.compile(r'<a href="'+W+r'"[^>]*>[^<]*</a>')
U=re.compile(W)
# display-title forms only: preceded by a space/quote/>, never by / _ % - (URLs, slugs, thumbs, files)
T=re.compile(r'(?<=[\s>"(])(?:[-\u2013\u2014]\s)?Wikipedia(?:,? the free encyclopedia)?(?=[\s.,"<(:)&]|$)')
def fix_titles(s):
    # remove the title word together with the one space before it; never touch other whitespace
    s=re.sub(r' ?(?<=[\s>"(])(?:[-\u2013\u2014]\s)?Wikipedia(?:,? the free encyclopedia)?(?=[\s.,"<(:)&]|$)','',s)
    s=re.sub(r' (?:[-\u2013\u2014]\s)?Wikipedia(?:,? the free encyclopedia)?(?=[\s.,"<(:)&]|$)','',s)
    s=re.sub(r'(?<=[>"(])(?:[-\u2013\u2014]\s)?Wikipedia(?:,? the free encyclopedia)? ?','',s)
    return s
files=subprocess.run(['git','grep','-il','wikipedia','--','*.html','*.js','*.json','*.xml',':!x/data/t/*',':!x/data/facets.json',':!memes/data/memes.json',':!tools/*'],capture_output=True,text=True).stdout.split()
tot=0
for f in files:
    s=open(f,encoding='utf-8').read(); o=s
    s=A.sub(lambda m:'<span class="ref-cut">'+topic(m)+'</span>',s)
    s=U.sub(topic,s)
    if f.startswith(('library/','pdfs.html','assets/search/','sitemaps/')): s=fix_titles(s)
    if s!=o:
        n=len(re.findall('wikipedia',o,re.I))-len(re.findall('wikipedia',s,re.I)); tot+=n
        print(f'{n:4d} {f}')
        if APPLY: open(f,'w',encoding='utf-8').write(s)
print('removed',tot)
