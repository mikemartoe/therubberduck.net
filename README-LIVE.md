# ON AIR · LIVE sign

A vintage light-box sign in the upper-left of every room landing page (homepage, Private Theater,
Listening Room, SCI[F] + OSS room, Drop Ledger, Meme Dump, Twitter/X Archive, DUCK SAUCE, Collectibles
(merch.html), Site Sponsors (sponsor.html), Red Pill Album (album.html), Drive-In (/watch/)). PC: just under the
header bar. Phones: inside the header bar, right of the logo.

- Script: `/assets/trd/onair.js` (CSS is inside it). Include on a page with
  `<script src="/assets/trd/onair.js?v=20261117r" defer data-trd-keep></script>`.
- Data: `/live.json`, fetched on load and every 2 minutes while the tab is open.

```json
{ "live": false, "liveUrl": "", "liveLabel": "", "liveStart": "", "liveEnd": "",
  "latestArticle": { "slug": "...", "title": "...", "url": "/newsroom/<slug>/", "publishedAt": "YYYY-MM-DD or ISO" } }
```

## New live link = edit ONE file (`/live.json`)
Mike sends a link to where he is speaking live -> set these fields in `live.json`, commit, push, purge Cloudflare:
```json
"live": true,
"liveUrl": "https://x.com/i/spaces/XXXX",
"liveLabel": "Live on X Spaces",
"liveStart": "2026-11-17T14:15:00-05:00",
"liveEnd":   "2026-11-17T17:00:00-05:00",
"replayUntil": "2026-11-24T23:59:00-05:00",
"replayLabel": "Listen to the replay",
```
Leave `latestArticle` alone. `liveStart` / `liveEnd` are ISO times with the offset (-05:00 in winter, -04:00 in summer).
- Before `liveStart`: sign lit, label **LIVE TODAY 2:15 PM ET** (or **LIVE TUE 2:15 PM ET** on an earlier day), click opens the link.
- `liveStart` .. `liveEnd`: label **LIVE NOW ON X**, click opens the link. Flips by itself at the start time, no deploy.
- Optional replay: between `liveEnd` and `replayUntil` the sign stays lit but calm (no flicker / pulse), label
  **LISTEN TO THE REPLAY** (`replayLabel`; phone sub-line "Replay"), click opens the same `liveUrl` (the X Space
  link plays the recording) in a new tab. The pop-up says "Missed it? Listen to the replay" with **Listen ›**.
  Leave `replayUntil` empty for no replay.
- After `liveEnd` (or after `replayUntil` when set): back to normal (new-dispatch / dim). No cleanup needed, but set `live` back to false later.
- Without `liveStart`/`liveEnd` it behaves like before (lit "live now" until `live` is set false).
- While upcoming/live, a small ON AIR pop-up shows bottom-left with one line and **Join** / **Set reminder**
  (opens the link in a new tab). Closing it is remembered per link (`localStorage["trd.onairPop.closed:<url>:<soon|live|replay>"]`).
  On the homepage it stays hidden while the Christmas bundle pop-up is open and appears after that is closed.
  It lifts itself above the Ledger phone nav pill / support button and the Listening Room player bar.
- Test any time without deploying: add `?onair-now=2026-11-17T14:25:00-05:00` to a page URL.

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
python3 tools/update-live-json.py --live "https://x.com/i/spaces/XXXX" --label "Live on X Spaces" \
  --start 2026-11-17T14:15:00-05:00 --end 2026-11-17T17:00:00-05:00
python3 tools/update-live-json.py --off
```
Commit + push `live.json`. GitHub Pages usually serves it within ~1–2 minutes; open pages pick it up within 2 more.

## Every DUCK SAUCE publish
Run `python3 tools/update-live-json.py` as the last step (sets `latestArticle` to the newest
`newsroom/<slug>/` story by schema `datePublished`). For a story filed today that carries an older
original X date, pass `--published-at 2026-11-09T18:00:00-05:00` so the 24-hour window counts from the
newsroom publish.
