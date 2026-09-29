#!/bin/bash
# Setup video skill dependencies
# Run once per machine: scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== Video Skill Setup ==="

# Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi
echo "✓ ffmpeg $(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')"

# Check ffprobe
if ! command -v ffprobe &>/dev/null; then
    echo "ERROR: ffprobe not found (should come with ffmpeg)"
    exit 1
fi
echo "✓ ffprobe available"

# Create venv
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating venv at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Install Python deps
echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Python dependencies installed"

# Check Ollama (optional, for describe command)
if command -v ollama &>/dev/null; then
    echo "✓ ollama available"
    if ollama list 2>/dev/null | grep -q llava; then
        echo "✓ llava model available"
    else
        echo "⚠ llava model not pulled. Run: ollama pull llava"
    fi
else
    echo "⚠ ollama not found. describe command won't work. Install with: brew install ollama"
fi

echo ""
echo "=== Setup complete ==="
echo "Usage: scripts/video_handler.py info <video>"
