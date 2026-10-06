#!/usr/bin/env bash
# Publish docs/wiki/ to the GitHub wiki. The wiki is kept as code in this repo so it is
# versioned and reviewed with everything else; this script mirrors it.
#
#   bash scripts/publish_wiki.sh
#
# One-time setup: open https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/wiki,
# click "Create the first page", save it (any text), then run this script.
set -euo pipefail
REPO="peytonbackus-spec/sardine-gtm-revops-toolkit"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if ! git clone --quiet "https://github.com/${REPO}.wiki.git" "$TMP" 2>/dev/null; then
  echo "Can't reach the wiki repo yet."
  echo "Open https://github.com/${REPO}/wiki, click 'Create the first page', Save, then re-run."
  echo "(GitHub Free doesn't offer wikis on private repos; the pages are readable in docs/wiki/.)"
  exit 1
fi

rsync -a --delete --exclude ".git" "$ROOT/docs/wiki/" "$TMP/"
cd "$TMP"
git add -A
if git diff --cached --quiet; then
  echo "Wiki already up to date."
  exit 0
fi
git commit --quiet -m "Sync wiki from docs/wiki @ $(git -C "$ROOT" rev-parse --short HEAD)"
git push --quiet origin HEAD
echo "Published: https://github.com/${REPO}/wiki"
