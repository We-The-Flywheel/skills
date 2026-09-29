---
name: video-analyze
description: >-
  Analyze video files with ffmpeg, Whisper, and LLaVA: metadata, transcription, scene detection, visual description. Use when the user asks about a video file or wants it transcribed or summarized. Never read video files directly.
department: media
---

# Video Analysis

## Overview

Analyze video files without loading binary data into context. Uses ffmpeg, mlx-whisper, PySceneDetect, and Ollama/LLaVA for comprehensive video understanding.

## Quick Reference

| Command | Description |
|---------|-------------|
| `info <file>` | Duration, resolution, codec, bitrate, fps, audio tracks |
| `transcribe <file>` | Speech-to-text with timestamps |
| `scenes <file>` | Scene boundary detection with timestamps |
| `describe <file>` | Visual description of key frames via LLaVA |

## Commands

### Video Info

```bash
scripts/video_handler.py info <video_file> [--summary]
```

Returns codec, resolution, duration, bitrate, fps, audio tracks. Use `--summary` for compact text output.

### Transcribe Speech

```bash
scripts/video_handler.py transcribe <video_file> [--language en] [--summary]
```

Extracts audio and runs mlx-whisper for speech-to-text. Returns timestamped segments.

Options:
- `--language LANG` - Force language (auto-detected by default)
- `--summary` - Compact text output (timestamps + text only)

### Detect Scenes

```bash
scripts/video_handler.py scenes <video_file> [--threshold 27.0] [--summary]
```

Detects scene boundaries using content-aware detection. Returns scene list with start/end timestamps and duration.

Options:
- `--threshold N` - Detection sensitivity (lower = more scenes, default: 27.0)
- `--summary` - Compact text output

### Describe Content

```bash
scripts/video_handler.py describe <video_file> [--interval 10] [--max-frames 10] [--summary]
```

Extracts key frames and describes each using Ollama LLaVA. Returns timestamped visual descriptions.

Options:
- `--interval N` - Seconds between frame samples (default: 10)
- `--max-frames N` - Maximum frames to analyze (default: 10)
- `--summary` - Compact text output

**Requires**: Ollama running with LLaVA model (`ollama pull llava`)

## Setup

Run the setup script on each machine:

```bash
scripts/setup.sh
```

This creates a local venv and installs dependencies.

## Dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| ffmpeg/ffprobe | Media processing | `brew install ffmpeg` (already installed) |
| mlx-whisper | Speech-to-text | Via setup.sh (Apple Silicon optimized) |
| scenedetect | Scene detection | Via setup.sh |
| ollama + llava | Visual descriptions | `brew install ollama && ollama pull llava` |

## Output Formats

### JSON (default)

Structured data suitable for programmatic use.

### Summary (`--summary`)

Compact text output optimized for LLM context. Reduces token usage significantly.

## Performance Notes

- `info`: Instant (~100ms, ffprobe only)
- `transcribe`: ~0.5x real-time on Apple Silicon (30s video → ~15s)
- `scenes`: ~2-5s for most videos
- `describe`: ~5-10s per frame (depends on Ollama/LLaVA speed)
- All outputs are text/JSON — never binary data
