# Web app (PWA) and push alerts: going live

Live since 2026-10-30 (Mike approved). Installed app opens /app/ (start_url); homepage layout unchanged; email digest hook stays off.

## Preview
- Site preview (this branch, noindex): https://trd-pwa-preview.therubberduck.workers.dev/ (Worker `trd-pwa-preview`, source `workers/trd-pwa-preview.js`)
- Push API preview: https://trd-push-preview.therubberduck.workers.dev/api/push/health (Worker `trd-push-preview`, KV `trd-push-preview-subs`, SEND_ENABLED=false so the crons only log)

## Going live
1. Merge branch `pwa-preview-20261030` into main (files: manifest.webmanifest, sw.js, offline.html, assets/trd/pwa.js, assets/trd/pwa.css, alerts/, images/app/, images/brand/social-*-20261030.png, data/deltas-index.json, data/drops-latest.json, head tags in index.html, ledger.html, deltas/index.html, q-proofs/index.html). /app/ (layout A) stays out unless Mike picks it.
2. Make the builders keep the changes: tools/seo-deltas-build.py (head tags, og:image, alerts line on the Deltas hub, data/deltas-index.json) and the drop build (data/drops-latest.json on every new drop). Other pages get the app by adding the same 6 head tags (or one line in sitenav.js).
3. Create KV namespace `trd-push-subs`; deploy `workers/trd-push.js` as Worker `trd-push` with bindings: KV SUBS; vars VAPID_PUBLIC_KEY, VAPID_SUBJECT=https://therubberduck.net/, SITE=https://therubberduck.net, ALLOWED_ORIGINS=https://therubberduck.net,https://www.therubberduck.net, SEND_ENABLED=true; secrets VAPID_PRIVATE_JWK and ADMIN_TOKEN (values in /workspace/.secrets/trd-push-vapid.json; same key pair as the preview, so preview subscriptions would carry over; generate a new pair only if the preview subscribers should be dropped).
4. Route: `therubberduck.net/api/push/*` -> `trd-push` (and `www.therubberduck.net/api/push/*` if www serves the site).
5. Crons on `trd-push`: `0 13 * * *` (Deltas digest, 9 AM New York in summer, 8 AM in winter) and `0,30 * * * *` (new-drop check). The first drop check only records the current latest drop, so nobody gets an alert for old drops.
6. Email digest: set `window.TRD_PWA_CONFIG = { mailerliteDeltasGroup: '<group id>' }` before pwa.js (or the default in pwa.js) once a MailerLite group "Daily Deltas" exists; the newsletter forms then gain a checked "Also send the daily Deltas digest" box. Sending the email itself is a MailerLite automation on that group (or a later Worker job using the MailerLite API key).
7. Delete preview Workers `trd-pwa-preview`, `trd-push-preview` and KV `trd-push-preview-subs`.
