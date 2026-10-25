# trd-visits (anonymous visit analytics), NOT DEPLOYED

What it stores: one row per page view / page leave (visible ms) / share tap, keyed by a random visit id that
expires after 30 min idle (assets/trd/visit.js). No IP, user agent, cookie or account. GPC/DNT browsers send nothing.

Deploy (only when Mike approves):
1. `npx wrangler d1 create trd-visits` and paste the id into wrangler.toml
2. `npx wrangler d1 execute trd-visits --remote --file schema.sql`
3. `npx wrangler secret put REPORT_KEY`
4. `npx wrangler deploy` (route therubberduck.net/api/v*; more specific than the trd-mobile-fix route, so it wins)
5. In assets/trd/visit.js set `ENDPOINT = '/api/v'`, commit, push.
Report: `curl -H "Authorization: Bearer $REPORT_KEY" https://therubberduck.net/api/v/report?days=30`
Rollback: set ENDPOINT back to '' (stops sending), then `npx wrangler delete trd-visits` if wanted.
Cost: Workers Free 100k requests/day; D1 Free 5 GB, 5M rows read/day, 100k rows written/day.
At ~3 rows per page view that is roughly 30k page views/day on the free tier; Workers Paid ($5/month) beyond that.
