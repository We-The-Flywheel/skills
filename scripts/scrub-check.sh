#!/usr/bin/env bash
# Leak-check: fail if any confidential/internal pattern appears in the repo.
# Run locally before pushing; also runs in CI on every PR/push.
#
# The allowed env-file reference is the literal token `~/.env.shared` (or
# `$HOME/.env.shared`). Internal env-file *paths* (e.g. /opt/security-mgmt/...)
# are caught by their path prefix below.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Forbidden patterns (extended regex). Word boundaries on short host names so
# substrings like "discussing"/"fuel"/"much" don't trigger false positives.
PATTERNS=(
  '\b(sin|hcm|fue|muc)\b'        # internal machine hostnames
  'sin:8300'                     # internal API host:port
  'flywheel\.bz'                 # internal domain
  'prommer\.net'                 # personal domain
  'nicoleprommer'                # personal domain
  'ctaio\.dev'                   # internal project domain
  'vietnamand'                   # internal project domain
  'agentic-coding'               # private config repo
  '/opt/(security-mgmt|growth-engine|email-agents)'  # private infra paths
  '/Users/(deploy|jesse)'        # absolute home paths
  '[A-Za-z0-9._%+-]+@(flywheel\.bz|prommer\.net)'    # internal emails
  '@thomas_prommer'              # personal handle
  '\bplannotator\b'              # internal plan-review tool
  '\b(beauty|health|dating|video|infra|content)-mgmt\b'  # personal management repos
)

JOINED="$(IFS='|'; echo "${PATTERNS[*]}")"

HITS=$(grep -rEnI "$JOINED" . \
  --exclude-dir=.git \
  --exclude-dir=node_modules \
  --exclude-dir=__pycache__ \
  --exclude='scrub-check.sh' || true)

if [ -n "$HITS" ]; then
  echo "❌ scrub-check FAILED — confidential/internal patterns found:"
  echo
  echo "$HITS"
  echo
  echo "Remove or genericize the above before publishing. See CONTRIBUTING.md."
  exit 1
fi

echo "✅ scrub-check passed — no confidential patterns found."
