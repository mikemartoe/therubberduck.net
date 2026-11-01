#!/usr/bin/env bash
# Nightly X archive sync, after Grok Bot has saved the fetched pages into a folder (see HOWTO.md, "Keeping the X archive current").
# Usage: tools/x_archive_nightly.sh <drop-folder> [--push]
# Without --push it stops after the local commit. With --push it tags the current origin/main as
# rollback-pre-xsync-YYYYMMDD (New York date), pushes the tag, then pushes the commit to main.
set -euo pipefail
cd "$(dirname "$0")/.."
DROP="${1:?drop folder}"; PUSH="${2:-}"
git fetch -q origin main
git merge -q --ff-only origin/main
python3 tools/x_archive_sync.py apply --drop "$DROP" | tee /tmp/x_archive_sync_last.json
python3 tools/x_archive_sync.py verify > /tmp/x_archive_verify_last.json || { cat /tmp/x_archive_verify_last.json; echo "verify failed, nothing committed"; exit 1; }
git add -A x sitemaps sitemap.xml assets/search/site-index.json -- $(git ls-files -m '*.html')
if git diff --cached --quiet; then echo "no new posts"; exit 0; fi
N=$(python3 -c "import json;print(json.load(open('x/data/meta.json'))['n'])")
git commit -q -m "X archive: nightly sync, $N posts through $(TZ=America/New_York date +%F)"
echo "committed $(git rev-parse --short HEAD)"
if [ "$PUSH" = "--push" ]; then
  TAG="rollback-pre-xsync-$(TZ=America/New_York date +%Y%m%d)"
  git rev-parse -q --verify "refs/tags/$TAG" >/dev/null || git tag "$TAG" origin/main
  git push -q origin "$TAG"
  git push -q origin HEAD:main
  echo "pushed to main; rollback tag $TAG"
fi
