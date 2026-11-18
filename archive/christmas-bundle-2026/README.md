# Christmas bundle campaign 2026 — index

Last updated Tuesday, November 17, 2026 (America/New_York, ET). No passwords, tokens or keys are in this file or folder.

## Live URLs
- Christmas page: https://therubberduck.net/christmas/
  - #christmas-bundle ($79), #christmas-bundle-big-duck ($129 Big Duck), #christmas-bundle-trd-mvp ($179 TRD-MVP)
- Homepage pop-up (full screen, homepage only, EXIT / Esc / tap outside close it, hidden 24h after close, off after Dec 25): https://therubberduck.net/
- Store lineup: https://therubberduck.net/merch.html#christmas-bundles (bundle rows unchanged)
- Old URLs (redirect to /christmas/): /christmas-preview-x7q4/ (keeps #hash), /christmas-bundle/ -> /christmas/#christmas-bundle
- Stripe checkouts:
  - $79: https://buy.stripe.com/4gMbJ189CcF2fldcM79IQ1n
  - $129 Big Duck: https://buy.stripe.com/7sY00j2PicF21un5jF9IQ1o
  - $179 TRD-MVP: https://buy.stripe.com/fZu3cv1Le7kI1un13p9IQ1p

## Stripe (live account acct_1NvT2xGC9fEXRvQS)
| Tier | Product | Price | Payment link |
|---|---|---|---|
| $79 bundle | prod_Ve6bIDCCRF0zF6 | price_1UcoOlGC9fEXRvQSv0Te9cmW | plink_1UcoP6GC9fEXRvQSHfC7D0bW |
| $129 Big Duck | prod_VeDt0oZq25R0Z3 | price_1UcvSBGC9fEXRvQSJY2Rxb5C | plink_1UcvSQGC9fEXRvQSZzUFFtmR |
| $179 TRD-MVP | prod_VeDt98kcSPNb2Q | price_1UcvSEGC9fEXRvQSRORBwJfM | plink_1UcvSXGC9fEXRvQSZqsxqBSU |

Custom fields: teecolor, teesize (Big Duck) / size "Size (tee + hoodie)" (TRD-MVP), hatcolor "Baseball cap color". US shipping, no shipping charge. $129 and $179 include the bundle-only bonus "+ FREE $50 ad on therubberduck.net, runs 90 days" (fine print is Mike's call).

## Site commits (repo github.com/mikemartoe/therubberduck.net, /workspace/trd-site)
| Step | Commit | Rollback tag (points at the commit before) |
|---|---|---|
| Tiers launch | ae36e20c1 | rollback-pre-xmas-tiers-20261117 -> 41b2cfa60 |
| Button text "See the $X bundle" | 8cae01ea3 | rollback-pre-xmas-buttons-20261117 -> ae36e20c1 |
| Private preview | 5226ed7b5 | — |
| Publish /christmas/ + pop-up v2 | f6d52745e | rollback-pre-xmas-popup2-20261117 -> 5226ed7b5 |
| Campaign source media archive | bd10be467 | rollback-pre-xmas-archive-20261117 -> f6d52745e |

Roll back the pop-up only: remove the `xmaspopup:begin … xmaspopup:end` block in index.html. Full rollback: `git checkout rollback-pre-xmas-popup2-20261117 -- index.html christmas-bundle/index.html …`, commit, push, purge Cloudflare (zone d0b522cc48a1425088c5c8760f92b72d).

## Site files
- /christmas/ page: trd-site/christmas/index.html (body has data-trd-full so the ON AIR sign loads after a pop-up click)
- Pop-up v2 code: trd-site/assets/trd/xmaspopup2.js (loaded from index.html)
- Store sections: trd-site/merch.html (xmasbundle block)
- Store images: trd-site/store-img/xmas-bundle-hero, xmas-bundle-big-duck-hero, xmas-bundle-trd-mvp-hero (.jpg/.webp)
- Share image: trd-site/images/share/christmas-bundle-og-20261117.jpg
- Sitemap: trd-site/sitemaps/shop.xml, sitemaps/all-urls.txt, sitemap.xml
- Source media copy (off-box in the git repo, not indexed; /archive/ is disallowed in robots.txt): trd-site/archive/christmas-bundle-2026/ (tiers heroes + hoodie mockups, images, promo videos and frames, redpill sticker finals, QR avatar options)

## Printful (store 18941423)
- New hoodie: sync product 495448573, Gildan 18500 White S–3XL, catalog variants 5522–5527, sync variants 5648884264–5648884269, front file 1091466582
- Bundle parts and print files: trd-merch/stripe-links.json (entries christmas-bundle, christmas-bundle-big-duck, christmas-bundle-trd-mvp); sticker print file 1114534794
- Mug, koozie and patch ship from other facilities (orders may come in more than one box). Patch and dark-cap thread may add a one-time $6.50 digitizing fee.

## Order forwarding (/workspace/trd-merch, text files covered by the nightly backup)
- forward_orders.py (part quantity support; size fallback) — backup forward_orders.py.bak-20261117-before-xmas-tiers
- stripe-links.json — backup stripe-links.json.bak-20261117-before-xmas-tiers
- printful-map.json (duck-hoodie) — backup printful-map.json.bak-20261117-before-hoodie
- FORWARDING.md ("Christmas bundle tiers" section) — backup FORWARDING.md.bak-20261117-before-xmas-tiers
- Dry run: tiers/forwarding-test/

## Campaign folder (/workspace/christmas-bundle-2026-11-17)
- tiers/PROPOSAL.md (original proposal), tiers/LIVE.md (tiers launch record), tiers/*.py (estimates, hero build, checks)
- tiers/tier2-big-duck-129-hero.jpg, tiers/tier3-trd-mvp-179-hero.jpg, tiers/old/tier3-head-duck-179-hero.jpg, tiers/hoodie-white-*.png
- images/ ($79 heroes and ads), promo/ (bundle-promo.mp4, bundle-promo-16x9.mp4, build.py, build_wide.py)
- popup-preview/ (preview shots), popup-live/ (live checks: verify.py and screenshots)
- ADS.md, PLAN.md, STRIPE-PAYLOADS.md, metrics-2026-11-17-1655.md

## Backups
- Text/scripts in /workspace go nightly to the private repo mikemartoe/trd-workfiles (see /workspace/trd-backup-tools). It skips media and secrets.
- Media for this campaign is kept in the site repo at archive/christmas-bundle-2026/.
- Secrets stay in /workspace/.secrets (never backed up, never copied here).
