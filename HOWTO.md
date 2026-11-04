# How to run therubberduck.net (backup instructions)

This file explains how the site works so anyone Duck trusts can keep it going without Grok Bot.

## Where the site lives
- The code and files are in the GitHub repo mikemartoe/therubberduck.net, which is public and on Duck's account.
- GitHub Pages publishes it for free from the `main` branch, root folder. The `.nojekyll` file must stay.
- Any change pushed to `main` goes live within a couple of minutes. The site keeps running with no credits anywhere.
- Only one helper should change the site at a time. Before you start, tell Duck and the other helper.

## The domain (GoDaddy, owned by Duck)
- Apex `therubberduck.net` has four A records: 185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153.
- `www` is a CNAME to `mikemartoe.github.io`.
- In the repo's Settings, under Pages, the custom domain is `therubberduck.net` with Enforce HTTPS turned on.

## Pages
- `index.html`: the homepage, with six doors and the X Archive bar.
- `videos.html` and `listening-room.html`: the Rumble videos and recordings. Each one needs a real overview, never a blank one.
- `memes.html` with `memes/data/memes.json` and `memes/web/`: the meme dump.
- `pdfs.html` with `scif/`: the SCIF PDF room. Big PDFs go next to last. GitHub won't accept files over 100 MB.
- `ledger.html` with `data/drops.js`: the Q drop ledger. Each drop links to its original post on the 4plebs archive and to the original anon research thread.
- `x/`: the searchable archive of every @TheRubberDuck79 post (the count is `n` in `x/data/meta.json`). Its media plays from X's own servers.
- Every page carries the GoatCounter visitor counter tag (therubberduck.goatcounter.com). Duck holds that login.

## Adding new memes
1. New memes go in `D:\meme\for-the-site` on Duck's laptop.
2. Copy only the new files somewhere you can run Python. You need `pip install opencv-python pytesseract pillow` and Tesseract OCR.
3. Run `tools/memes-intake.py` to make web copies in `memes/web/` and add records to `memes/data/memes.json`. Skip files that are already there.
4. Run `python tools/clean_tags.py memes/data/memes.json` to strip junk tags.
   Then run `python tools/meme-share-build.py`. It makes the share page for each meme (`memes/share/<id>.html`) and a letterboxed preview card (`memes/card/<id>.jpg`) for tall or square memes, so X, Facebook and Reddit show that meme instead of the generic card.
5. Check `memes.html` locally (`python -m http.server`), then commit and push to `main`.
- Never put people's names in meme tags.

## The X archive
`tools/x-archive-build.py` rebuilds `x/` from an X data export. The full export is on Duck's D: drive at `D:\TheRubberDuck\x-archive-2026-09-26`.

### Keeping the X archive current (nightly)
`tools/x-archive-build.py` is only for a full rebuild from a new export. New posts are added with `tools/x_archive_sync.py`, which never renumbers or rewrites existing posts.
1. Get the new posts. Run `python3 tools/x_archive_sync.py plan` and fetch with those arguments: X API v2 "posts by user" (`GET /2/users/1254803542914850816/tweets`) with `since_id` set to the last archived post, following `next_token` until there is none. Grok Bot does this with its built-in X tool (`get_users_posts`), 25 posts per call. Save every raw response as a `.json` file in one folder. No key is ever stored in this repo.
2. `tools/x_archive_nightly.sh <folder>` adds the posts (skips any already there, by post id), checks everything (`python3 tools/x_archive_sync.py verify`) and commits. Add `--push` to publish: it first tags the old `main` as `rollback-pre-xsync-YYYYMMDD`.
3. What it updates: `x/data` (posts, search, filters, downloads), the month pages under `x/archive/` and the month list, `sitemaps/x.xml`, `sitemaps/all-urls.txt`, `sitemap.xml`, and the post count and date range in `x/index.html`, the page footers and `assets/search/site-index.json`.
4. Posts are kept exactly as posted, except Wikipedia links, which become plain "(ref: Topic)". Hand fixes in month pages (such as Wayback links) are carried over; if a page was changed in another way the script stops and says which page.
5. To undo a sync: `git push -f origin rollback-pre-xsync-YYYYMMDD:main` (only after telling Duck).
- Limits: X returns only the newest 3,200 posts of a timeline, so if the sync stops for weeks, use a new X data export instead. Like and repost counts are as of the night they were fetched. Posts deleted on X later stay in the archive.

## Rules from Duck
- Show Duck a preview before publishing anything new.
- Keep personal email addresses and private client details out of the site.
- Nothing on the site may be served from Duck's own PC.
- Never put passwords or keys in this repo or in a chat.
