#!/usr/bin/env python3
"""Build locale trees for therubberduck.net and patch English originals with hreflang.

Only chrome, homepage, merch/shop, sponsor, join and process are localized.
Archive bodies (drops, X posts, PDFs, DUCK SAUCE articles) stay English.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = "https://therubberduck.net"
CATALOG_PATH = Path(__file__).with_name("catalog.json")

# (dir prefix, html lang, hreflang, English label, native label)
LOCALES = [
    ("", "en", "en", "English", "English"),
    ("en-au", "en-AU", "en-AU", "English (Australia)", "English (Australia)"),
    ("es", "es", "es", "Spanish", "Español"),
    ("fr", "fr-FR", "fr-FR", "French", "Français"),
    ("fr-ca", "fr-CA", "fr-CA", "French (Canada)", "Français (Canada)"),
    ("de", "de", "de", "German", "Deutsch"),
    ("nl", "nl-NL", "nl-NL", "Dutch", "Nederlands"),
    ("ja", "ja", "ja", "Japanese", "日本語"),
]
LOCALE_DIRS = [loc[0] for loc in LOCALES if loc[0]]

SOURCES = [
    "index.html",
    "merch.html",
    "sponsor.html",
    "join.html",
    "process.html",
] + [f"shop/{p.name}/index.html" for p in sorted((ROOT / "shop").iterdir()) if (p / "index.html").is_file()]

# Never rewrite these terms, even if a shorter catalog key would overlap.
GLOSSARY = [
    "The Rubber Duck™",
    "The Rubber Duck",
    "THE RUBBER DUCK™",
    "THE RUBBER DUCK",
    "TRD Collectibles",
    "TRD-MVP",
    "TRD-022",
    "TRD",
    "DUCK SAUCE",
    "Q drop",
    "Q drops",
    "The Red Pill Album",
    "Red Pill Album",
    "Red Pill Room",
    "anon mission",
    "EO Library",
    "Drop Ledger",
    "The Drop Ledger",
    "SCI[F]",
    "SCI[F] Library",
    "The Rubber Duck Christmas Bundles",
    "The Rubber Duck Christmas Bundle",
    "Big Duck",
    "Signed Baseball Cap",
    "Signed Duck Tee",
    "Signed Trucker",
    "Duck Baseball Cap",
    "Duck Koozie 6-Pack",
    "Duck Koozie",
    "Duck Patch",
    "Duck Magnet",
    "Duck Sticker",
    "Duck Coffee Mug",
    "Premium Wool Cap",
    "Trucker Hat",
    "Red Pill Tee",
    "Gumroad",
    "Stripe",
    "Buy Me a Coffee",
    "Back the Duck",
    "@TheRubberDuck79",
    "@TheRubberDuck78",
    "therubberduk@gmail.com",
    "therubberduck.net",
]

NOTE = {
    "en-au": "Australian English edition. Prices are in USD. View the original.",
    "es": "Traducción asistida por máquina. Ver el original en inglés.",
    "fr": "Traduction assistée par ordinateur. Voir l’original en anglais.",
    "fr-ca": "Traduction assistée par ordinateur. Voir l’original anglais.",
    "de": "Maschinenunterstützte Übersetzung. Zum englischen Original.",
    "nl": "Machine-ondersteunde vertaling. Naar het Engelse origineel.",
    "ja": "機械支援翻訳です。英語の原文はこちら。",
}


def en_url(rel: str) -> str:
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return SITE + "/" + rel[: -len("index.html")]
    return SITE + "/" + rel


def loc_url(prefix: str, rel: str) -> str:
    if not prefix:
        return en_url(rel)
    if rel == "index.html":
        return f"{SITE}/{prefix}/"
    if rel.endswith("/index.html"):
        return f"{SITE}/{prefix}/" + rel[: -len("index.html")]
    return f"{SITE}/{prefix}/{rel}"


def loc_path(prefix: str, rel: str) -> Path:
    if not prefix:
        return ROOT / rel
    return ROOT / prefix / rel


def hreflang_links(rel: str) -> str:
    lines = []
    for prefix, _lang, hreflang, _elabel, _nlabel in LOCALES:
        lines.append(f'<link rel="alternate" hreflang="{hreflang}" href="{loc_url(prefix, rel)}">')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{en_url(rel)}">')
    return "\n".join(lines)


def switcher_html(current_prefix: str, rel: str) -> str:
    parts = ['<nav class="sf-langs" aria-label="Language">']
    for prefix, lang, hreflang, _elabel, nlabel in LOCALES:
        href = loc_url(prefix, rel).replace(SITE, "") or "/"
        cur = ' aria-current="page"' if prefix == current_prefix else ""
        parts.append(
            f'<a href="{href}" lang="{lang}" hreflang="{hreflang}"{cur}>{nlabel}</a>'
        )
    parts.append("</nav>")
    return "".join(parts)


def translation_note(prefix: str, rel: str) -> str:
    if not prefix:
        return ""
    text = NOTE[prefix]
    href = en_url(rel).replace(SITE, "") or "/"
    # Link the last clause-ish by wrapping the whole sentence's "original" target
    return (
        f'<p class="trd-i18n-note">{text} '
        f'<a href="{href}" lang="en" hreflang="en">English</a></p>'
    )


def absolutize(html: str, prefix: str) -> str:
    """Rewrite root-relative-needed links so locale pages don't resolve under /fr/."""

    def href_sub(m: re.Match) -> str:
        attr, q, url = m.group(1), m.group(2), m.group(3)
        if re.match(r"^(https?:|mailto:|tel:|#|//)", url):
            return m.group(0)
        if url.startswith("/"):
            # If this path has a locale version, point at it; else keep English root path
            return m.group(0)
        # relative
        if url.startswith("images/") or url.startswith("assets/") or url.startswith("store-img/") or url.startswith("fonts/"):
            return f"{attr}={q}/{url}{q}"
        # relative page
        return f"{attr}={q}/{url}{q}"

    html = re.sub(
        r'\b(href|src|action)=(["\'])(?!https?:|mailto:|tel:|#|//)([^"\']+)\2',
        href_sub,
        html,
    )
    # Point locale-available paths at the locale copy
    available = {en_url(s).replace(SITE, "") or "/" for s in SOURCES}
    # also directory forms
    def localize_root(m: re.Match) -> str:
        attr, q, url = m.group(1), m.group(2), m.group(3)
        path = url.split("#")[0].split("?")[0]
        if path.rstrip("/") + "/" in available or path in available or path + "/" in available:
            if prefix:
                locp = f"/{prefix}{path if path.startswith('/') else '/' + path}"
                rest = url[len(path):]
                return f"{attr}={q}{locp}{rest}{q}"
        return m.group(0)

    if prefix:
        html = re.sub(
            r'\b(href)=(["\'])(/(?:merch\.html|sponsor\.html|join\.html|process\.html|shop/[^"\']+|)?(?:#[^"\']*)?)(\2)',
            lambda m: m.group(0)
            if False
            else _localize_href(m, prefix, available),
            html,
        )
        # broader
        html = re.sub(
            r'\b(href)=(["\'])(/[^"\']+)\2',
            lambda m: _localize_href(m, prefix, available),
            html,
        )
    return html


def _localize_href(m: re.Match, prefix: str, available: set[str]) -> str:
    attr, q, url = m.group(1), m.group(2), m.group(3)
    if url.startswith(tuple(f"/{p}/" for p in LOCALE_DIRS)) or url in {f"/{p}" for p in LOCALE_DIRS}:
        return m.group(0)
    path = url.split("#")[0].split("?")[0]
    candidates = {path, path.rstrip("/") + "/", path + ("/" if not path.endswith("/") and not path.endswith(".html") else "")}
    if path == "/":
        return f"{attr}={q}/{prefix}/{q}" if "href" == attr else m.group(0)
    if any(c in available for c in candidates):
        rest = url[len(path):]
        return f"{attr}={q}/{prefix}{path}{rest}{q}"
    return m.group(0)


def protect_glossary(html: str) -> tuple[str, list[str]]:
    tokens = []
    out = html
    for i, term in enumerate(sorted(GLOSSARY, key=len, reverse=True)):
        token = f"@@GLOSSARY{i}@@"
        if term in out:
            out = out.replace(term, token)
            tokens.append((token, term))
        # entity form of trademark
        entity = term.replace("™", "&trade;")
        if entity != term and entity in out:
            tok = f"@@GLOSSARYE{i}@@"
            out = out.replace(entity, tok)
            tokens.append((tok, entity))
    return out, tokens


def restore_glossary(html: str, tokens: list[str]) -> str:
    for token, term in tokens:
        html = html.replace(token, term)
    return html


def _wordish(s: str) -> bool:
    return re.fullmatch(r"[A-Za-z]+(?:[A-Za-z0-9\'-]*[A-Za-z0-9])?", s) is not None


def _sub_key(html: str, en: str, tr: str) -> str:
    if _wordish(en):
        return re.sub(r'(?<![A-Za-z0-9])' + re.escape(en) + r'(?![A-Za-z0-9])', tr, html)
    return html.replace(en, tr)


def _apply_to_chunk(html: str, catalog: dict[str, str]) -> str:
    html, toks = protect_glossary(html)
    for en, tr in sorted(catalog.items(), key=lambda kv: len(kv[0]), reverse=True):
        if not en or not tr or en == tr:
            continue
        keys = [en]
        en_tok = en
        for token, term in toks:
            if term in en_tok:
                en_tok = en_tok.replace(term, token)
        if en_tok != en:
            keys.append(en_tok)
        for a, b in (
            ("'", "&#39;"),
            ("'", "&#x27;"),
            ("'", "&apos;"),
            ("'", "&rsquo;"),
            ("’", "&rsquo;"),
            ("‘", "&lsquo;"),
            ("™", "&trade;"),
            ("·", "&middot;"),
            ("&", "&amp;"),
            ("—", "&mdash;"),
            ("–", "&ndash;"),
            ("×", "&times;"),
            ('"', "&quot;"),
            ("©", "&copy;"),
        ):
            for k in list(keys):
                enc = k.replace(a, b)
                if enc != k:
                    keys.append(enc)
        seen = set()
        for k in keys:
            if k and k not in seen:
                seen.add(k)
                tr_p = tr
                for token, term in toks:
                    tr_p = tr_p.replace(term, token)
                html = _sub_key(html, k, tr_p)
    return restore_glossary(html, toks)


def apply_catalog(html: str, catalog: dict[str, str]) -> str:
    """Translate visible HTML only. Leave <script> and <style> untouched so JS stays valid."""
    parts = re.split(r'(?is)(<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>)', html)
    out = []
    for part in parts:
        if part.lower().startswith('<script') or part.lower().startswith('<style'):
            out.append(part)
        else:
            out.append(_apply_to_chunk(part, catalog))
    return ''.join(out)


def set_lang_and_canonical(html: str, prefix: str, rel: str, lang: str) -> str:
    html = re.sub(r'<html[^>]*>', f'<html lang="{lang}">', html, count=1)
    canon = loc_url(prefix, rel)
    if re.search(r'<link\s+rel=["\']canonical["\']', html, re.I):
        html = re.sub(
            r'<link\s+rel=["\']canonical["\'][^>]*>',
            f'<link rel="canonical" href="{canon}">',
            html,
            count=1,
            flags=re.I,
        )
    else:
        html = html.replace("</head>", f'<link rel="canonical" href="{canon}">\n</head>', 1)
    # strip existing alternate hreflang, then insert a fresh cluster after canonical
    html = re.sub(r'\s*<link\s+rel=["\']alternate["\']\s+hreflang="[^"]+"[^>]*>', "", html, flags=re.I)
    links = hreflang_links(rel)
    html = re.sub(
        r'(<link rel="canonical"[^>]*>)',
        r"\1\n" + links,
        html,
        count=1,
    )
    return html


def set_in_language(html: str, lang: str) -> str:
    def fix(m: re.Match) -> str:
        block = m.group(0)
        if "inLanguage" in block:
            block = re.sub(r'"inLanguage"\s*:\s*"[^"]*"', f'"inLanguage": "{lang}"', block)
        else:
            # insert after first object open if it looks like a graph or WebPage
            block = re.sub(
                r'("@type"\s*:\s*"(?:WebPage|CollectionPage|WebSite|Product)"\s*,)',
                r'\1 "inLanguage": "%s",' % lang,
                block,
                count=0,
            )
        return block

    return re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', fix, html)


def inject_css(html: str) -> str:
    tag = '<link rel="stylesheet" href="/assets/trd/i18n.css?v=20261121a">'
    if "i18n.css" in html:
        return html
    if "</head>" in html:
        return html.replace("</head>", tag + "\n</head>", 1)
    return html


def inject_note_and_switcher(html: str, prefix: str, rel: str) -> str:
    note = translation_note(prefix, rel)
    sw = switcher_html(prefix, rel)
    if "sf-langs" not in html:
        if '<div class="sf-legal">' in html:
            html = html.replace('<div class="sf-legal">', sw + '\n<div class="sf-legal">', 1)
        elif "</footer>" in html:
            html = html.replace("</footer>", sw + "\n</footer>", 1)
    if prefix and note and "trd-i18n-note" not in html:
        if '<div class="sf-legal">' in html:
            html = html.replace('<div class="sf-legal">', note + '\n<div class="sf-legal">', 1)
        elif "<footer" in html:
            html = re.sub(r"<footer([^>]*)>", r"<footer\1>\n" + note, html, count=1)
    return html


def transform(src_html: str, prefix: str, rel: str, lang: str, catalog: dict[str, str]) -> str:
    html = src_html
    html = set_lang_and_canonical(html, prefix, rel, lang)
    html = inject_css(html)
    html = set_in_language(html, lang)
    if prefix:
        html = apply_catalog(html, catalog)
        html = absolutize(html, prefix)
    html = inject_note_and_switcher(html, prefix, rel)
    return html


def load_catalog() -> dict[str, dict[str, str]]:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    # { "Videos": { "fr": "Vidéos", ... }, ... } -> per-locale maps
    per: dict[str, dict[str, str]] = {d: {} for d in LOCALE_DIRS}
    for en, locs in data.items():
        if en.startswith("_"):
            continue
        for prefix, tr in locs.items():
            if prefix in per and tr:
                per[prefix][en] = tr
    return per


def validate_hreflang(written: list[tuple[str, str, Path]]) -> int:
    """Each generated/English page must cite every locale URL, and those files must exist."""
    errors = 0
    expected = {}
    for prefix, rel, path in written:
        expected[(prefix, rel)] = path
    for prefix, rel, path in written:
        html = path.read_text(encoding="utf-8")
        for op, _lang, hreflang, *_ in LOCALES:
            url = loc_url(op, rel)
            if f'hreflang="{hreflang}" href="{url}"' not in html:
                print(f"MISSING hreflang {hreflang} on {path.relative_to(ROOT)}", file=sys.stderr)
                errors += 1
        if f'hreflang="x-default" href="{en_url(rel)}"' not in html:
            print(f"MISSING x-default on {path.relative_to(ROOT)}", file=sys.stderr)
            errors += 1
        can = loc_url(prefix, rel)
        if f'rel="canonical" href="{can}"' not in html:
            print(f"BAD canonical on {path.relative_to(ROOT)}", file=sys.stderr)
            errors += 1
    return errors


def write_locales_sitemap(rels: list[str]) -> None:
    urls = []
    for rel in rels:
        for prefix in LOCALE_DIRS:
            urls.append(loc_url(prefix, rel))
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        body.append(f"  <url><loc>{u}</loc><lastmod>2026-11-21</lastmod></url>")
    body.append("</urlset>\n")
    (ROOT / "sitemaps" / "locales.xml").write_text("\n".join(body), encoding="utf-8")
    index = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    loc = "https://therubberduck.net/sitemaps/locales.xml"
    if loc not in index:
        index = index.replace(
            "</sitemapindex>",
            f'  <sitemap><loc>{loc}</loc><lastmod>2026-11-21</lastmod></sitemap>\n</sitemapindex>',
        )
        (ROOT / "sitemap.xml").write_text(index, encoding="utf-8")


def main() -> int:
    catalog = load_catalog()
    written: list[tuple[str, str, Path]] = []
    for rel in SOURCES:
        src = ROOT / rel
        if not src.is_file():
            print("missing source", rel, file=sys.stderr)
            continue
        original = src.read_text(encoding="utf-8")
        # Patch English original with hreflang + switcher + css (do not translate)
        en_html = transform(original, "", rel, "en", {})
        src.write_text(en_html, encoding="utf-8")
        written.append(("", rel, src))
        for prefix, lang, _h, _e, _n in LOCALES:
            if not prefix:
                continue
            html = transform(original, prefix, rel, lang, catalog.get(prefix, {}))
            dest = loc_path(prefix, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")
            written.append((prefix, rel, dest))
            print("wrote", dest.relative_to(ROOT))
    write_locales_sitemap(SOURCES)
    err = validate_hreflang(written)
    print(f"wrote {len(written)} pages, hreflang errors={err}")
    return 1 if err else 0


if __name__ == "__main__":
    raise SystemExit(main())
