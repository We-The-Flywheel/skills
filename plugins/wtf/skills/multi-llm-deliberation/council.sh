#!/bin/bash
# Multi-LLM Deliberation — self-contained wrapper
# Calls council.py directly via OpenRouter API (no backend needed)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUESTION="${1:-}"

if [ -z "$QUESTION" ]; then
    echo "Error: No question provided. Usage: /multi-llm-deliberation \"Your question here\"" >&2
    exit 1
fi

# Load API key if not in env
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    for envfile in "$HOME/.env.shared"; do
        if [ -f "$envfile" ]; then
            OPENROUTER_API_KEY=$(grep -m1 '^OPENROUTER_API_KEY=' "$envfile" | cut -d= -f2- | tr -d '"' | tr -d "'")
            export OPENROUTER_API_KEY
            break
        fi
    done
fi

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "Error: OPENROUTER_API_KEY not found in env or .env.shared files" >&2
    exit 1
fi

exec python3 "$SCRIPT_DIR/council.py" "$QUESTION"
