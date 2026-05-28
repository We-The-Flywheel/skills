#!/usr/bin/env bash
# One-time bootstrap for the visual-qa skill on a fresh machine.
# Installs Playwright + downloads the Chromium binary.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> npm install"
npm install --no-audit --no-fund --loglevel=error

echo "==> playwright install chromium"
npx playwright install chromium

echo "✓ visual-qa ready."
