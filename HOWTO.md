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
- `ledger.html` with `data/drops.js`: the Q drop ledger. Each drop links to qalerts.app.
- `x/`: the searchable archive of all 61,225 @TheRubberDuck79 posts. Its media plays from X's own servers.
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

## Rules from Duck
- Show Duck a preview before publishing anything new.
- Keep personal email addresses and private client details out of the site.
- Nothing on the site may be served from Duck's own PC.
- Never put passwords or keys in this repo or in a chat.
