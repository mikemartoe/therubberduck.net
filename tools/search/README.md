# Unified full-text search

The header search still uses `assets/search/site-index.json` for titles. This
index adds the text inside the rooms. The visitor's browser does the search.
Nothing about the query is sent anywhere.

The generated files are not in git. `main` is already close to the GitHub Pages
size limit, so the index is built on a machine that has the sources and then
served from a URL. One constant picks that URL.

## Build

From the repo root:

```bash
node tools/search/build-unified.mjs
```

That reads the live SCI[F] text from
`https://scif-search.therubberduck.net/scif-search/2beb375c5b/` and writes
`search/unified/` (gitignored). Pass `--scif` with another base URL, or a
local folder that has `search/manifest.json` and `text/`, to point it elsewhere.

```bash
node tools/search/build-unified.mjs --scif ./some-local-scif
node tools/search/build-unified.mjs --scif https://HOST/scif-search/<build>/
```

Check the exclusion list without building the index:

```bash
node tools/search/exclude.test.mjs
```

Count fetches for a few queries after a build:

```bash
node tools/search/measure.mjs
```

## The one URL

In `assets/trd/fulltext-search.js`:

```javascript
var TRD_FULLTEXT_BASE = 'https://scif-search.therubberduck.net/fulltext/981b404b79/';
```

That is the only place the index is loaded from. The build still writes a local
copy at `search/unified/` for a preview. Do not commit that directory. A new
build gets a new content hash; point the constant at
`https://scif-search.therubberduck.net/fulltext/<hash>/`.

## Upload to R2

This preview does not create a bucket, upload anything, or spend money. When
you are ready, from a machine that already has credentials:

```bash
# Long-lived shard and passage files.
aws s3 sync search/unified s3://BUCKET/unified \
  --endpoint-url https://ACCOUNT.r2.cloudflarestorage.com \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "manifest.json"

# The manifest changes every build, so revalidate it.
aws s3 cp search/unified/manifest.json s3://BUCKET/unified/manifest.json \
  --endpoint-url https://ACCOUNT.r2.cloudflarestorage.com \
  --cache-control "public, max-age=60"
```

`wrangler r2 object put` works too if that is how the account is set up. Then
set `TRD_FULLTEXT_BASE` to the public URL of that prefix.

R2 storage and the requests that read it are the cost. There is no search
server and no query log.

## What a hit opens

| Room | Link |
| --- | --- |
| SCI[F] | `/pdfs.html?open=TRD-0001&p=12` |
| Q drop | `/drops/123/` |
| Executive order | `/eo-library/14362/` plus a text fragment when a section has no anchor |
| X post | `/x/post.html?id=…` |
| Meme | `/memes/share/<id>.html` when the image has OCR text |
| Lyric | `/album/<slug>/#t=<seconds>` |
| Recording | `/listening-room.html#vol=<id>` and `&t=<seconds>` on Rumble |
| Video | `/watch/<id>/` (title and description only) |

Words are combined: every word has to appear in the same passage. Very common
words are left out of the index (the stop list in the manifest).

## Exclusion

`tools/search/exclude.mjs` always leaves out `TRD-0087` and `TRD-0129`.
TRD-0129 is a saved 404 page. Its card stays in the room. Its text is not indexed.
`DROP_LIBRARY_TITLE` is one line in that file. It is `true`, so
`/library/epstein-black-book/` is not added to this index. The existing
`assets/search/site-index.json` row is not edited.

Thin and junk PDF pages are re-read by `tools/scif-ocr-repair.py` into
`/workspace/scif-ocr-repair/`. That folder is not uploaded.

## Header

`assets/trd/sitenav.js` keeps the title search, the SCI[F] "Inside" rows, and
the X Archive row. It adds an "In the text" group from this index and a link
to `/search.html`, which is `noindex`. Room search pages are unchanged apart
from that one excluded document.
