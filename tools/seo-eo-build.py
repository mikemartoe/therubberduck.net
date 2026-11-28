#!/usr/bin/env python3
"""Build one static, crawlable HTML page per Executive Order (/eo-library/<n>/),
a crawlable HTML directory inside /eo-library/index.html, and sitemaps/eo.xml.

Data sources (already used by /eo-library/eo-library.js):
  - eo-library/data/eos.js      (window.TRD_EOS, 512 records)
  - eo-library/data/eo-texts.js (window.TRD_EO_TEXTS, full text per order)

Idempotent: safe to re-run whenever new Executive Orders are added.
"""
from __future__ import annotations

import datetime
import html
import json
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://therubberduck.net"
ORG_ID = f"{SITE}/#org"
SITE_ID = f"{SITE}/#website"
R2_PDF = "https://memes.therubberduck.net/eo-library/pdfs/eo-"
TODAY = datetime.date.today().isoformat()

TAG_LABEL = {
    "cartels": "Cartels",
    "immigration": "Immigration",
    "election": "Elections",
    "sanctions": "Sanctions",
    "china": "China",
    "iran": "Iran",
    "israel": "Israel",
    "energy": "Energy",
    "trade": "Trade",
    "healthcare": "Healthcare",
    "military": "Military",
    "intelligence": "Intelligence",
    "civil-service": "Civil service",
    "trafficking": "Trafficking",
    "justice": "Justice",
    "education": "Education",
    "environment": "Environment",
    "economy": "Economy",
    "covid": "COVID",
    "records": "Records",
    "human-rights": "Human rights",
    "terrorism": "Terrorism",
    "foreign-policy": "Foreign policy",
    "housing": "Housing",
    "tech": "Technology",
    "crime": "Crime",
    "regulatory": "Regulation",
    "emergency": "Emergency",
}

STATUS_LABEL = {
    "active": "In force",
    "amended": "Amended",
    "revoked": "Revoked",
    "superseded": "Superseded",
}

E = lambda s: html.escape(str(s or "").replace("\r\n", "\n").replace("\r", "\n"), quote=True)


def clip(s: str, n: int = 158) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if len(s) <= n:
        return s
    cut = s[: n - 1].rsplit(" ", 1)[0].rstrip(",;:-")
    return (cut or s[: n - 1]) + "\u2026"


def write_if_changed(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = text.encode("utf-8")
    if path.exists() and path.read_bytes() == raw:
        return False
    path.write_bytes(raw)
    return True


def load_data():
    eos_raw = (ROOT / "eo-library" / "data" / "eos.js").read_text(encoding="utf-8")
    m_eos = re.search(r"window\.TRD_EOS=(\[.*\]);\s*$", eos_raw, re.S)
    if not m_eos:
        raise SystemExit("Could not parse window.TRD_EOS in eo-library/data/eos.js")
    eos = json.loads(m_eos.group(1))

    txt_raw = (ROOT / "eo-library" / "data" / "eo-texts.js").read_text(encoding="utf-8")
    m_txt = re.search(r"window\.TRD_EO_TEXTS=(\{.*\});\s*$", txt_raw, re.S)
    if not m_txt:
        raise SystemExit("Could not parse window.TRD_EO_TEXTS in eo-library/data/eo-texts.js")
    texts = json.loads(m_txt.group(1))
    return eos, texts


def format_full_text(raw: str, expected_title: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b.strip() for b in re.split(r"\n{2,}", raw.strip()) if b.strip()]
    if not blocks:
        return ""
    parts = []
    # Block 0 always begins with the title on line 1 followed by the preamble.
    first_lines = [ln.strip() for ln in blocks[0].splitlines() if ln.strip()]
    if first_lines and first_lines[0] == expected_title.strip():
        parts.append(f'<p class="eo-doc-title">{E(first_lines[0])}</p>')
        if len(first_lines) > 1:
            parts.append(f"<p>{E(' '.join(first_lines[1:]))}</p>")
    else:
        parts.append(f"<p>{E(' '.join(first_lines))}</p>")

    # Detect trailing signature block (typically DONALD J. TRUMP / The White House, / Date.)
    body_blocks = blocks[1:]
    sign_blocks = []
    if len(body_blocks) >= 3 and body_blocks[-3].strip().upper() == "DONALD J. TRUMP":
        sign_blocks = body_blocks[-3:]
        body_blocks = body_blocks[:-3]

    for b in body_blocks:
        lines = [ln.strip() for ln in b.splitlines() if ln.strip()]
        parts.append(f"<p>{E(' '.join(lines))}</p>")

    if sign_blocks:
        sign_html = "".join(
            f"<p>{E(' '.join(ln.strip() for ln in sb.splitlines() if ln.strip()))}</p>"
            for sb in sign_blocks
        )
        parts.append(f'<div class="eo-doc-sign">{sign_html}</div>')

    return "\n        ".join(parts)


NAV_HTML = """<header class="trd-nav" id="trd-nav"><div class="tn-in">
<a class="tn-logo" href="/" aria-label="The Rubber Duck, home"><img src="/assets/trd/img/duck-banner.webp" width="40" height="34" alt=""><span class="tn-wm" aria-hidden="true">THE RUBBER DUCK<sup>&trade;</sup></span></a>
<nav class="tn-links" id="tn-links" aria-label="Rooms"><a href="/videos.html">Videos</a><a href="/listening-room.html">Recordings</a><a href="/pdfs.html">PDFs</a><a href="/eo-library/" aria-current="page">EO Library</a><a href="/ledger.html">Drop Ledger</a><a href="/ledger.html?view=photos">Photo Search</a><a href="/memes.html">Memes</a><a href="/x/">X Archive</a><a href="/newsroom.html">DUCK SAUCE</a><a href="/merch.html#anon-mission">Book</a></nav>
<form class="tn-search" id="tn-form" role="search" action="/x/" method="get"><svg class="tn-mag" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg><input class="tn-q" id="tn-q" name="q" type="search" placeholder="Search the archive" aria-label="Search the whole archive" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="tn-res" aria-autocomplete="list"><div class="tn-res" id="tn-res" role="listbox" aria-label="Search results" hidden></div></form>
<button class="tn-btn tn-menu" id="tn-menu" type="button" aria-expanded="false" aria-controls="tn-links" aria-label="Menu"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></button>
<button class="tn-btn tn-sb" id="tn-sbtn" type="button" aria-expanded="false" aria-label="Search the archive"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M15.5 15.5 21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg></button>
</div></header>
<div class="eol-cheat" aria-hidden="true"><span></span><span></span><span></span><span></span></div>"""

FOOTER_HTML = """<footer class="site-foot">
  <div class="sf-in">
    <div class="sf-brand">
      <a class="sf-logo" href="/"><img src="/assets/trd/img/duck-banner.webp" width="268" height="230" alt="The Rubber Duck, site logo, link to home" loading="lazy" decoding="async">THE RUBBER DUCK&trade;</a>
      <p>An open archive of the Q era: every Q drop, the shows, X Space recordings, PDFs, memes, articles and X posts.</p>
      <a class="sf-x" href="https://x.com/TheRubberDuck79" target="_blank" rel="noopener me"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M18.2 2.3h3.4l-7.4 8.4 8.7 11.5h-6.8l-5.3-7-6.1 7H1.3l7.9-9L.9 2.3h7l4.8 6.4zm-1.2 17.9h1.9L7.1 4.2H5.1z"/></svg>Follow @TheRubberDuck79</a>
    </div>
    <nav class="sf-col" aria-label="The archive">
      <h2>The archive</h2>
      <ul><li><a href="/videos.html">Videos</a></li><li><a href="/listening-room.html">Recordings</a></li><li><a href="/pdfs.html">PDFs</a></li><li><a href="/eo-library/">EO Library</a></li><li><a href="/ledger.html">Drop Ledger</a></li><li><a href="/memes.html">Memes</a></li><li><a href="/x/">X Archive</a></li><li><a href="/newsroom.html">DUCK SAUCE</a></li><li><a href="/album.html">The Red Pill Album</a></li></ul>
    </nav>
    <nav class="sf-col" aria-label="support the mission">
      <h2>Support</h2>
      <ul><li><a href="/sponsor.html">Sponsor the Site</a></li><li><a href="/merch.html">TRD Collectibles</a></li><li><a href="https://rubberduck41.gumroad.com/l/ttmhx" target="_blank" rel="noopener">The book (Gumroad)</a></li><li><a href="https://buymeacoffee.com/re7l3hzgju/membership" target="_blank" rel="noopener">become a member</a></li><li><a href="https://buymeacoffee.com/re7l3hzgju" target="_blank" rel="noopener">support the mission</a></li></ul>
    </nav>
    <div class="sf-col">
      <h2>Contact</h2>
      <ul><li><a href="https://x.com/TheRubberDuck79" target="_blank" rel="noopener">Message @TheRubberDuck79 on X</a></li><li><a href="https://x.com/TheRubberDuck79" target="_blank" rel="noopener">Order and sponsor questions on X</a></li><li><button class="sf-btn" type="button" data-sug-open>Suggestion box</button></li></ul>
    </div>
  </div>
  <div class="sf-substack" role="region" aria-label="Subscribe by email on Substack">
  <iframe data-src="https://therubberduck78.substack.com/embed" width="480" height="260" style="border: 1px solid #EEE; background: white; max-width: 100%; width: 480px; height: 260px;" frameborder="0" scrolling="no" loading="lazy" title="Subscribe to The Rubber Duck on Substack"></iframe><noscript><iframe src="https://therubberduck78.substack.com/embed" width="480" height="260" style="border: 1px solid #EEE; background: white; max-width: 100%; width: 480px; height: 260px;" frameborder="0" scrolling="no" loading="lazy" title="Subscribe to The Rubber Duck on Substack"></iframe></noscript><script>(function(){var f=document.querySelector(".sf-substack iframe[data-src]");if(!f)return;function go(){if(!f.src||f.src==="about:blank"){f.src=f.getAttribute("data-src");}}if(!("IntersectionObserver" in window)){go();return;}var o=new IntersectionObserver(function(e){if(e[0].isIntersecting){o.disconnect();go();}},{rootMargin:"400px 0px"});o.observe(f);})();</script>
</div>
<div class="sf-legal">
    <p>Colors on this page are sampled from the official U.S. Air Force VC-25B Executive Airlift rendering (DVIDS VIRIN 260218-O-F3227-1001, February 18, 2026). Each order links to the official Federal Register record and PDF, which carries the printed presidential signature. Texts are from the American Presidency Project and the Federal Register; computer-captured text can contain errors, so quote the official PDF when it matters. Q connections are to matching words, names, or phrases in the drop text, with a link to the drop.</p>
    <p>&copy; 2026 The Rubber Duck&trade;. All rights reserved.</p>
  </div>
</footer>"""


def build_eo_page(r: dict, raw_text: str, prev_r: dict | None, next_r: dict | None) -> str:
    n = r["n"]
    url = f"{SITE}/eo-library/{n}/"
    term_label = "Second term" if r["term"] == 2 else "First term"
    status_key = r.get("status") or "active"
    status_text = STATUS_LABEL.get(status_key, status_key.capitalize())
    status_note = r.get("statusNote") or ""
    full_status = f"{status_text}. {status_note}" if status_note else f"{status_text}."

    title = f"Executive Order {n}: {r['title']} | The Rubber Duck\u2122"
    og_title = f"Executive Order {n}: {r['title']}"
    desc = clip(
        f"Executive Order {n} ({r['dateLabel']}), signed by President Donald J. Trump: {r['summary']}",
        158,
    )
    og_desc = clip(
        f"Executive Order {n} ({r['dateLabel']}), signed by President Donald J. Trump ({r['citation']}). {r['summary']}",
        200,
    )

    graph = [
        {
            "@type": "Organization",
            "@id": ORG_ID,
            "name": "The Rubber Duck",
            "url": f"{SITE}/",
            "sameAs": [
                "https://x.com/TheRubberDuck79",
                "https://x.com/TheRubberDuck78",
                "https://rumble.com/user/TheRubberDuck78",
            ],
        },
        {
            "@type": "WebSite",
            "@id": SITE_ID,
            "url": f"{SITE}/",
            "name": "The Rubber Duck",
            "publisher": {"@id": ORG_ID},
        },
        {
            "@type": "WebPage",
            "@id": f"{url}#page",
            "url": url,
            "name": og_title,
            "description": desc,
            "datePublished": r["date"],
            "dateModified": r.get("published") or r["date"],
            "isPartOf": {"@id": f"{SITE}/eo-library/#page"},
            "publisher": {"@id": ORG_ID},
            "inLanguage": "en",
            "about": {"@type": "Person", "name": "Donald J. Trump"},
            "citation": r.get("citation") or "",
            **({"isBasedOn": r["frUrl"]} if r.get("frUrl") else {}),
            "breadcrumb": {"@id": f"{url}#crumbs"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#crumbs",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Executive Order Library", "item": f"{SITE}/eo-library/"},
                {"@type": "ListItem", "position": 3, "name": f"EO {n}", "item": url},
            ],
        },
    ]
    ld = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    tags = r.get("tags") or []
    tags_html = (
        '<div class="eo-tags" aria-label="Topics">'
        + "".join(f'<span class="eo-tag">{E(TAG_LABEL.get(t, t))}</span>' for t in tags)
        + "</div>"
        if tags
        else ""
    )

    actions = [
        f'<a class="eo-btn eo-btn-pri" href="{E(R2_PDF + str(n) + ".pdf")}" target="_blank" rel="noopener">Signed Federal Register PDF</a>'
    ]
    if r.get("frUrl"):
        actions.append(
            f'<a class="eo-btn" href="{E(r["frUrl"])}" target="_blank" rel="noopener">Federal Register page</a>'
        )
    if r.get("pdfUrl"):
        actions.append(
            f'<a class="eo-btn" href="{E(r["pdfUrl"])}" target="_blank" rel="noopener">govinfo.gov official file</a>'
        )
    actions.append(f'<a class="eo-btn" href="/eo-library/#eo-{n}">Open binder in library</a>')

    q_html = ""
    if r.get("q"):
        q_cards = "".join(
            '<article class="q-card">'
            f'<a href="/drops/{q["n"]}/">Q drop {q["n"]}</a>'
            + (f'<p class="q-why">{E(q["why"])}</p>' if q.get("why") else "")
            + f'<blockquote>{E(q["quote"])}</blockquote>'
            "</article>"
            for q in r["q"]
        )
        q_html = f"""
  <section class="eo-box" aria-labelledby="eo-q-h">
    <h2 id="eo-q-h">Q drop connections</h2>
    {q_cards}
  </section>"""

    full_text_html = format_full_text(raw_text, r["title"])

    pager_links = []
    if prev_r:
        pager_links.append(
            f'<a href="/eo-library/{prev_r["n"]}/" rel="prev">&larr; EO {prev_r["n"]}: {E(clip(prev_r["title"], 48))}</a>'
        )
    else:
        pager_links.append('<a href="/eo-library/">All 512 Executive Orders</a>')
    pager_links.append('<a href="/eo-library/">Executive Order Library</a>')
    if next_r:
        pager_links.append(
            f'<a href="/eo-library/{next_r["n"]}/" rel="next">EO {next_r["n"]}: {E(clip(next_r["title"], 48))} &rarr;</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Rubber Duck&trade;">
<meta property="og:title" content="{E(og_title)}">
<meta property="og:description" content="{E(og_desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/eo-library/img/signing.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1245">
<meta property="og:image:height" content="700">
<meta property="og:image:alt" content="President Donald J. Trump signing an executive order.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@TheRubberDuck79">
<meta name="twitter:title" content="{E(og_title)}">
<meta name="twitter:description" content="{E(og_desc)}">
<meta name="twitter:image" content="{SITE}/eo-library/img/signing.jpg">
<meta name="twitter:image:alt" content="President Donald J. Trump signing an executive order.">
<link rel="icon" href="/favicon.ico">
<link rel="stylesheet" href="/assets/trd/sitenav.css?v=20261126sl">
<link rel="stylesheet" href="/assets/trd/suggest.css">
<link rel="stylesheet" href="/assets/trd/support-strip.css?v=20261120a">
<link rel="stylesheet" href="/eo-library/eo-library.css?v=779d94d30a">
<link rel="stylesheet" href="/eo-library/eo-page.css?v=20261121a">
<script>window.trdNav||(function(){{var s=document.createElement('script');s.src='/assets/trd/sitenav.js?v=6ecf81cc49';s.setAttribute('data-trd-keep','');document.head.appendChild(s);}})();</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@graph":{ld}}}</script>
<script data-goatcounter="https://therubberduck.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="/assets/trd/analytics.js?v=20261121a" data-trd-keep></script>
</head>
<body class="eol">
<a class="skip" href="#eo-main">Skip to order</a>

{NAV_HTML}

<main class="eo-wrap" id="eo-main">
  <nav class="eo-crumbs" aria-label="Breadcrumb">
    <a href="/">Home</a> <span aria-hidden="true">&rsaquo;</span>
    <a href="/eo-library/">Executive Order Library</a> <span aria-hidden="true">&rsaquo;</span>
    <span>Executive Order {n}</span>
  </nav>

  <header class="eo-head">
    <div class="eo-head-top">
      <img class="eo-head-seal" src="/eo-library/img/presidential-seal.svg" width="64" height="64" alt="Seal of the President of the United States">
      <div>
        <p class="eo-kicker">The White House &middot; {term_label} &middot; President Donald J. Trump</p>
        <p class="eo-num-tag">Executive Order {n}</p>
      </div>
    </div>
    <h1>{E(r['title'])}</h1>
    <dl class="eo-meta">
      <div><dt>Executive Order</dt><dd>{n}</dd></div>
      <div><dt>Signing date</dt><dd>{E(r['dateLabel'])}</dd></div>
      <div><dt>President</dt><dd>Donald J. Trump</dd></div>
      <div><dt>Term</dt><dd>{term_label}</dd></div>
      <div><dt>Federal Register</dt><dd>{E(r['citation'])} &middot; Doc. {E(r['docNumber'])}</dd></div>
      <div><dt>Published</dt><dd>{E(r.get('published') or r['date'])}</dd></div>
    </dl>
    {tags_html}
    <div class="eo-actions">
      {"".join(actions)}
    </div>
  </header>

  <section class="eo-box" aria-labelledby="eo-sum-h">
    <h2 id="eo-sum-h">What this order does</h2>
    <p>{E(r['summary'])}</p>
    <p class="eo-status-note"><strong>Status:</strong> {E(full_status)}</p>
  </section>{q_html}

  <section class="eo-paper-wrap" aria-labelledby="eo-text-h">
    <div class="eo-paper">
      <div class="eo-paper-head">
        <h2 id="eo-text-h">Full official text &middot; Executive Order {n}</h2>
        <p class="eo-paper-cite">{E(r['citation'])} &middot; {E(r['dateLabel'])}</p>
      </div>
      <div class="eo-doc-body">
        {full_text_html}
      </div>
    </div>
  </section>

  <nav class="eo-pager" aria-label="Adjacent executive orders">
    {"".join(pager_links)}
  </nav>
</main>

<aside class="eol-ss-wrap">
  <aside class="trd-ss" id="trdSupportStrip" data-ss-kind="eol" data-ss-id="eol" aria-label="Support the library">
    <div class="trd-ss-in">
      <p class="trd-ss-line">&#x203C;&#xFE0F; this library stays free.</p>
      <div class="trd-ss-acts">
        <a class="trd-ss-b" href="/merch.html">&#x1F449;&#x1F3FC; Grab a shirt in the store</a>
        <span class="trd-ss-dot" aria-hidden="true">&middot;</span>
        <a class="trd-ss-b" href="https://buymeacoffee.com/re7l3hzgju" target="_blank" rel="noopener">&#x2615; support the mission</a>
        <span class="trd-ss-dot" aria-hidden="true">&middot;</span>
        <button type="button" class="trd-ss-b" id="eolShareBtn">&#x1F517; Share this order</button>
      </div>
      <p class="eol-share-msg" id="eolShareMsg" hidden></p>
    </div>
  </aside>
</aside>

{FOOTER_HTML}

<script src="/assets/trd/suggest.js" defer></script>
<script>
(function(){{
  var b=document.getElementById('eolShareBtn'),m=document.getElementById('eolShareMsg');
  if(!b)return;
  b.addEventListener('click',async function(){{
    var url={json.dumps(url)},title={json.dumps(og_title)};
    try{{if(navigator.share)await navigator.share({{title:title,url:url}});else{{await navigator.clipboard.writeText(url);if(m){{m.hidden=false;m.textContent='Link copied.';}}}}}}
    catch(e){{try{{await navigator.clipboard.writeText(url);if(m){{m.hidden=false;m.textContent='Link copied.';}}}}catch(e2){{}}}}
  }});
}})();
</script>
</body>
</html>
"""


def build_directory_html(eos: list[dict]) -> str:
    groups = defaultdict(list)
    for r in eos:
        groups[(r["term"], r["year"])].append(r)
    keys = sorted(groups.keys(), key=lambda k: (-k[1], -k[0]))
    sections = []
    for term, year in keys:
        rows = sorted(groups[(term, year)], key=lambda x: (-x["n"]))
        label = f"{'Second term' if term == 2 else 'First term'} \u00b7 {year} ({len(rows)})"
        items = "".join(
            f'<li><a href="/eo-library/{r["n"]}/"><span class="eol-dir-n">EO {r["n"]}</span>{E(r["title"])}</a>'
            f'<span class="eol-dir-date">{E(r["dateLabel"])}</span></li>'
            for r in rows
        )
        sections.append(f'<div class="eol-dir-group"><h3>{E(label)}</h3><ul class="eol-dir-list">{items}</ul></div>')
    return (
        "<!-- eo-index:begin -->\n"
        '  <details class="eol-dir" id="eolDirectory">\n'
        f'    <summary>Browse all {len(eos)} Executive Orders (complete text index &amp; direct links)</summary>\n'
        '    <p class="eol-dir-note">Every order signed by President Donald J. Trump has its own readable page with summary, Federal Register links, Q drop connections, and full official text.</p>\n'
        + "".join(sections)
        + "\n  </details>\n"
        "  <!-- eo-index:end -->"
    )


def update_library_index(eos: list[dict]) -> bool:
    path = ROOT / "eo-library" / "index.html"
    h = path.read_text(encoding="utf-8")

    css_link = '<link rel="stylesheet" href="/eo-library/eo-page.css?v=20261121a">'
    if "/eo-library/eo-page.css" not in h:
        m = re.search(r'<link rel="stylesheet" href="/eo-library/eo-library\.css\?v=[^"]+">', h)
        if not m:
            raise SystemExit("Could not find eo-library.css link in eo-library/index.html")
        needle = m.group(0)
        h = h.replace(needle, needle + "\n" + css_link, 1)

    dir_block = build_directory_html(eos)
    if "<!-- eo-index:begin -->" in h:
        h = re.sub(r"<!-- eo-index:begin -->.*?<!-- eo-index:end -->", lambda _m: dir_block, h, count=1, flags=re.S)
    else:
        marker = "</main>"
        if marker not in h:
            raise SystemExit("Could not find </main> in eo-library/index.html")
        h = h.replace(marker, "  " + dir_block + "\n" + marker, 1)

    return write_if_changed(path, h)


def write_sitemap(eos: list[dict]) -> tuple[bool, bool]:
    # Sort descending by EO number (newest first)
    ordered = sorted(eos, key=lambda r: -r["n"])
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for r in ordered:
        lm = TODAY
        lines.append(f"  <url><loc>{SITE}/eo-library/{r['n']}/</loc><lastmod>{lm}</lastmod></url>")
    lines.append("</urlset>\n")
    sm_changed = write_if_changed(ROOT / "sitemaps" / "eo.xml", "\n".join(lines))

    idx_path = ROOT / "sitemap.xml"
    idx = idx_path.read_text(encoding="utf-8")
    idx = re.sub(r"\n?\s*<sitemap><loc>[^<]*/sitemaps/eo\.xml</loc>.*?</sitemap>", "", idx, flags=re.S)
    entry = f"  <sitemap><loc>{SITE}/sitemaps/eo.xml</loc><lastmod>{TODAY}</lastmod></sitemap>\n</sitemapindex>"
    idx = idx.replace("</sitemapindex>", entry, 1)
    idx_changed = write_if_changed(idx_path, idx)
    return sm_changed, idx_changed


def main() -> int:
    eos, texts = load_data()
    # Sort ascending by EO number for prev/next navigation
    by_n = sorted(eos, key=lambda r: r["n"])
    written = 0
    for i, r in enumerate(by_n):
        raw_text = texts.get(str(r["n"])) or ""
        if not raw_text.strip():
            raise SystemExit(f"Missing full text for EO {r['n']}")
        prev_r = by_n[i - 1] if i > 0 else None
        next_r = by_n[i + 1] if i + 1 < len(by_n) else None
        page_html = build_eo_page(r, raw_text, prev_r, next_r)
        out = ROOT / "eo-library" / str(r["n"]) / "index.html"
        if write_if_changed(out, page_html):
            written += 1

    idx_updated = update_library_index(by_n)
    sm_changed, sm_idx_changed = write_sitemap(by_n)
    print(
        json.dumps(
            {
                "orders": len(by_n),
                "pages_written": written,
                "eo_library_index_updated": idx_updated,
                "eo_sitemap_updated": sm_changed,
                "sitemap_index_updated": sm_idx_changed,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
