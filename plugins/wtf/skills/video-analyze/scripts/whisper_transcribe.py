#!/usr/bin/env python3
"""Standalone whisper transcription script - called by video_handler.py."""
import json
import os
import sys

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# Redirect stderr to devnull during import and transcription to suppress progress bars
import io  # noqa: E402

import mlx_whisper  # noqa: E402

wav_path = sys.argv[1]
model = sys.argv[2] if len(sys.argv) > 2 else "mlx-community/whisper-large-v3-turbo"
language = sys.argv[3] if len(sys.argv) > 3 else None

# Suppress progress bars and "Detected language" that go to stdout/stderr
old_stdout = sys.stdout
sys.stdout = io.StringIO()
old_stderr = sys.stderr
sys.stderr = io.StringIO()

try:
    result = mlx_whisper.transcribe(
        wav_path,
        path_or_hf_repo=model,
        language=language if language != "None" else None,
        verbose=False,
    )
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

output = {
    "language": result.get("language", "unknown"),
    "segments": [
        {
            "start": round(s["start"], 2),
            "end": round(s["end"], 2),
            "text": s["text"].strip(),
        }
        for s in result.get("segments", [])
    ],
    "text": result.get("text", "").strip(),
}
print(json.dumps(output))
