#!/usr/bin/env bash
# Upload the SCI[F] search data built by tools/scif-fulltext-build.py to Cloudflare R2 (bucket trd-scif-search,
# served at https://scif-search.therubberduck.net/scif-search/<build id>/{search,text}/...).
# Needs `wrangler login` (OAuth); no keys are stored anywhere. Usage: tools/scif-search-publish.sh <build id> [out dir] [parallel]
# <build id> is printed by the build ("R2 prefix: scif-search/<id>/"). Old build folders can stay (they are immutable).
set -euo pipefail
ID="${1:?build id}"; OUT="${2:-/workspace/scif-search-out}"; P="${3:-16}"
export ID OUT
cd "$(mktemp -d)"; echo '{"name":"r2work","private":true}' > package.json; mkdir -p node_modules/.cache
up() { f="$1"; rel="${f#$OUT/}"; for i in 1 2 3; do
  npx wrangler r2 object put "trd-scif-search/scif-search/$ID/$rel" --file "$f" --content-type "application/json; charset=utf-8" \
    --cache-control "public, max-age=31536000, immutable" --remote >/dev/null 2>&1 && return 0; sleep 2; done; echo "FAILED $rel" >&2; return 1; }
export -f up
find "$OUT" -type f -name '*.json' | xargs -P "$P" -I{} bash -c 'up "$@"' _ {}
printf 'User-agent: *\nDisallow: /\n' > robots.txt
npx wrangler r2 object put trd-scif-search/robots.txt --file robots.txt --content-type "text/plain; charset=utf-8" --cache-control "public, max-age=3600" --remote >/dev/null
echo "uploaded $(find "$OUT" -type f -name '*.json' | wc -l) files under scif-search/$ID/"
