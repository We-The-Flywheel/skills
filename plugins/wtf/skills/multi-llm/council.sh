#!/bin/bash
# Multi-LLM Deliberation — self-contained wrapper
# council.py resolves its own credentials (OPENROUTER_API_KEY, or a gateway URL +
# MULTILLM_GATEWAY_TOKEN) from the environment or ~/.env.shared.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUESTION="${1:-}"

if [ -z "$QUESTION" ]; then
    echo "Error: No question provided. Usage: /wtf:multi-llm \"Your question here\"" >&2
    exit 1
fi

exec python3 "$SCRIPT_DIR/council.py" "$QUESTION"
