# ON AIR · LIVE sign

A vintage light-box sign in the upper-left of every room landing page (homepage, Private Theater,
Listening Room, SCI[F], Drop Ledger, Meme Dump, Twitter/X Archive, DUCK SAUCE). PC: just under the
header bar. Phones: inside the header bar, right of the logo.

- Script: `/assets/trd/onair.js` (CSS is inside it). Include on a page with
  `<script src="/assets/trd/onair.js?v=20261109" defer data-trd-keep></script>`.
- Data: `/live.json`, fetched on load and every 2 minutes while the tab is open.

```json
{ "live": false, "liveUrl": "", "liveLabel": "",
  "latestArticle": { "slug": "...", "title": "...", "url": "/newsroom/<slug>/", "publishedAt": "YYYY-MM-DD or ISO" } }
```

## When it lights up
1. `live: true` with a `liveUrl` → lit, label **LIVE NOW** (or `liveLabel`), click opens `liveUrl` (new tab if off-site).
2. Otherwise, the newest article lights it (label **NEW DISPATCH**, click opens it) when the visitor has not
   seen it yet AND it was published in the last 24 hours, or the visitor has been here before and this
   article is newer than the last one they saw (stored in `localStorage["trd-onair-seen"]`).
   Clicking the sign or opening `/newsroom.html` marks it seen.
3. Else it stays dim (unlit). On PC the dim sign fades away once you scroll; a lit sign stays.
   Respects `prefers-reduced-motion` (no flicker / glow pulse).

## Go live / end live
```
python3 tools/update-live-json.py --live "https://x.com/i/broadcasts/XXXX" --label "LIVE FROM THE BEACH"
python3 tools/update-live-json.py --off
```
Commit + push `live.json`. GitHub Pages usually serves it within ~1–2 minutes; open pages pick it up within 2 more.

## Every DUCK SAUCE publish
Run `python3 tools/update-live-json.py` as the last step (sets `latestArticle` to the newest
`newsroom/<slug>/` story by schema `datePublished`). For a story filed today that carries an older
original X date, pass `--published-at 2026-11-09T18:00:00-05:00` so the 24-hour window counts from the
newsroom publish.
