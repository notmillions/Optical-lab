#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
web_dir="$repo_root/apps/web"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to verify the Vercel frontend build" >&2
  exit 1
fi

cd "$web_dir"
npm ci --no-audit --no-fund
npm run typecheck
npm test
npm run build

if [[ ! -f dist/index.html ]]; then
  echo "Vite build did not produce apps/web/dist/index.html" >&2
  exit 1
fi

echo "Vercel frontend build check passed: apps/web/dist/index.html"
