# Archived: the Spotify "Personal Playlist" cassette (homepage)

Taken off the homepage on 2026-11-01 at Mike's request. Nothing was deleted: the assets are still where
they were and every removed line is saved in this folder, so it can be brought back.

Last commit with it live: `fa19b6f62` (also tagged `rollback-pre-hoverbadge-20261101`).

## What it was
- A tape-case spine (`a.spine.tcase.tc-pl`, "SIDE B · Personal Playlist · On Spotify") under the hero button
  in the left column of the homepage room.
- Clicking it swapped tapes: the playlist cassette slid out of its case into the Walkman deck, and the
  Red Pill Album tape went back into the case (the case then read "SIDE A · The Red Pill Album").
- With the playlist in the deck, a Spotify embed (iFrame API, 80/152/352 px) sat in the deck's tape window
  (on phones, full width under the deck) with an "Open the full playlist on Spotify" link bar; the deck keys
  and the Duck Pod player drove Spotify (track list from a JSON snapshot).
- Hovering the case showed the playlist J-card face (`face-playlist.webp`) in the floating hover card.

## Files in this folder
| File | What |
|---|---|
| `index.before-removal.html.txt` | The whole homepage exactly as it was (commit `fa19b6f62`). `.txt` so it is never served as a page. |
| `tcase.html.txt` | The tape-case markup (old index.html lines 808-820, inside `<header class="hello">` after `<p class="hello-cta">`). Also removed: `<span class="kp-pl">Press play</span>` inside the deck's `.key-play` (line 840). |
| `tcase.css` | All CSS removed, with old line numbers: `a.tcase` (79), the playlist tape + Spotify window + link bar (539-570), the case spine and its two colourways + `caseTake` animation (636-668), size tweaks (678, 690), reduced motion (695), Walkman-window placement of the Spotify block (725-730). |
| `tape-swap.js` | All JS removed, with old line numbers: the `is-pl` guards in the deck script (1001-1003, 1011-1013), `.tcase` in the hover binding (1116), the `tcase` branch in `go()` (1170-1173), `button.tcase` / `is-pl` in the click handler (1190-1194), case-width fitting in the hero script (1233-1253) and the whole two-tapes swap module (1254-1438: Spotify embed, iFrame API, Duck Pod source `PL`, swap animation, `window.__trdSwapTape`, `window.__trdTapeMode`, `window.__trdTapeBusy`). |

## Assets (left in place, not deleted)
- `/assets/trd/img/cassettes/face-playlist.webp` (J-card face for the hover card)
- `/assets/trd/img/playlist-cover-192.jpg` (cover in the Duck Pod while the playlist plays)
- `/assets/trd/playlist-trd.json` (track list snapshot: t=title, a=artist, u=Spotify track id, s=seconds, p=playable)
- `/assets/trd/img/duck-banner.webp`, `/assets/trd/img/rpa-pill.webp` (spine icons; still used elsewhere)
- Spotify playlist: `https://open.spotify.com/playlist/4lWQJV4n3mnIvp0y4biUqZ` (embed: `/embed/playlist/4lWQJV4n3mnIvp0y4biUqZ`)
- `assets/trd/duckpod.js` still has the generic `trdPod.useSource()` / `dropSource()` API the playlist used.
- Other pages that link the Spotify playlist were not touched.

## Tracking events it sent (GoatCounter)
- `click/tape-swap` — "Homepage: load Personal Playlist" / "Homepage: load Red Pill Album"
- `click/playlist-spotify` — "Homepage: open the full playlist on Spotify"

## How to restore it
1. Paste `tcase.html.txt` (without its first comment line) back into `index.html` inside `<header class="hello">`,
   right after the `<p class="hello-cta">…</p>` line. Put `<span class="kp-pl">Press play</span>` back after
   `<span class="kp-on">Open player</span>` in the deck's `.key-play`.
2. Paste the blocks from `tcase.css` back into the homepage `<style>` (anywhere after the base `.spine` rules;
   the old line numbers show where each block was).
3. JS (in the main homepage `<script>`):
   - Paste the "two tapes" module (the 1254-1438 block of `tape-swap.js`) right before the closing `</script>`
     of that script, and the hero `fitCase` part (1247-1252) back into the hero IIFE.
   - In the hover-card code: add `, .tcase` to the `querySelectorAll('a.spine, a.deck')` in `bind()`, and add
     `window.__trdTapeBusy||` to the first check in `placeFace()`.
   - In `go()`: add back, as its first lines after `closeFace();`:
     `if(host.classList.contains('tcase')&&window.__trdSwapTape){if(window.trdTrack)window.trdTrack('click/tape-swap','Homepage: load '+(window.__trdTapeMode()==='rp'?'Personal Playlist':'Red Pill Album'));window.__trdSwapTape();return;}`
   - In the click handler: restore `var shelfT=...closest('button.tcase')`, `if(deck&&deck.classList.contains('is-pl')&&!face)deck=null;`
     and `var host=spine||deck||shelfT;`; in the deck script restore the two `is-pl` early returns.
   - Hover-card badge: give the tape case its own wording in `badgeFor()` (e.g. `Click to load` / `Tap to load`),
     and mark the deck card inert (no badge, no click) while `deck.classList.contains('is-pl')` (the deck has no
     link then).
4. Easiest alternative: diff `index.before-removal.html.txt` against the current `index.html` and re-apply only
   the playlist hunks.
5. Test locally (`python3 -m http.server`), desktop and phone: swap both ways, Spotify plays in the window,
   deck keys pause it, the album player pauses Spotify, no layout gap, one-screen room on 1280x720.

## Adding a new cassette room spine (generic, no playlist code needed)
Each room is one `<a class="spine tN" href="room.html">` inside `.stack-a` or `.stack-b` (`<nav class="stacks">`):
1. Copy an existing spine line (e.g. `t5`) into the stack where it should go and change: class `tN` (next number),
   `href`, `TRD-00N` in `.sp-cat`, the `.sp-ic` icon, `.sp-n` title, `.sp-s` subtitle, and the `.sp-mk` word (Stereo / Type II).
2. Give it a J-card face: a 560x872 webp in `/assets/trd/img/cassettes/` referenced from its
   `<span class="spine-face"><img data-src="…?v=1" …></span>`. The hover card, its "Click to enter" / "Tap to enter"
   badge, tap-tap entry and the one-card-at-a-time rules pick it up automatically (they bind every `a.spine`).
3. Add colours like the others: `.tN .sp{background:…;color:…}`, `.tN .sp::before{…}` (the edge stripe),
   `.tN .sp-n{…}`, `.tN .sp-s{…}`, `.tN .sp-go{…}`, plus a hand-stacked offset (`.stack-a .spine:nth-child(n){--off;--rot;--lift}`).
4. Keep the two stacks even (3+3 now; 4+4 if two rooms are added) so the room stays balanced, then check
   1440x900, 1280x720 (the shortest laid-out screen: the room must still fit the first screen) and a phone.
