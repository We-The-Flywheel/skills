#!/usr/bin/env python3
"""
Claude Code skill handler for /video commands.

Usage:
    video_handler.py info <file> [--summary]
    video_handler.py transcribe <file> [--language LANG] [--summary]
    video_handler.py scenes <file> [--threshold N] [--summary]
    video_handler.py describe <file> [--interval N] [--max-frames N] [--summary]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


VENV_PYTHON = str(Path(__file__).parent / ".venv" / "bin" / "python")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")


def run_cmd(cmd, check=True, capture=True, timeout=300):
    """Run a shell command and return stdout."""
    result = subprocess.run(
        cmd, capture_output=capture, text=True, check=check, timeout=timeout
    )
    return result.stdout.strip() if capture else None


def ffprobe_json(file_path):
    """Get ffprobe output as JSON."""
    out = run_cmd([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(file_path)
    ])
    return json.loads(out)


def cmd_info(args):
    """Get video metadata via ffprobe."""
    probe = ffprobe_json(args.file)
    fmt = probe.get("format", {})
    streams = probe.get("streams", [])

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    info = {
        "file": str(args.file),
        "duration_seconds": float(fmt.get("duration", 0)),
        "duration_human": _format_duration(float(fmt.get("duration", 0))),
        "size_bytes": int(fmt.get("size", 0)),
        "size_human": _format_size(int(fmt.get("size", 0))),
        "bitrate_kbps": int(fmt.get("bit_rate", 0)) // 1000,
        "format": fmt.get("format_long_name", fmt.get("format_name", "unknown")),
    }

    if video_streams:
        v = video_streams[0]
        info["video"] = {
            "codec": v.get("codec_name"),
            "width": int(v.get("width", 0)),
            "height": int(v.get("height", 0)),
            "fps": _parse_fps(v.get("r_frame_rate", "0/1")),
            "pixel_format": v.get("pix_fmt"),
        }

    info["audio_tracks"] = []
    for a in audio_streams:
        info["audio_tracks"].append({
            "codec": a.get("codec_name"),
            "sample_rate": int(a.get("sample_rate", 0)),
            "channels": int(a.get("channels", 0)),
            "language": a.get("tags", {}).get("language", "unknown"),
        })

    if args.summary:
        lines = [f"File: {info['file']}"]
        lines.append(f"Duration: {info['duration_human']} | Size: {info['size_human']} | Bitrate: {info['bitrate_kbps']} kbps")
        if "video" in info:
            v = info["video"]
            lines.append(f"Video: {v['codec']} {v['width']}x{v['height']} @ {v['fps']:.1f} fps")
        for i, a in enumerate(info["audio_tracks"]):
            lines.append(f"Audio {i}: {a['codec']} {a['sample_rate']}Hz {a['channels']}ch ({a['language']})")
        print("\n".join(lines))
    else:
        print(json.dumps(info, indent=2))


def cmd_transcribe(args):
    """Transcribe speech using mlx-whisper."""
    # Extract audio to temp WAV
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        run_cmd([
            "ffmpeg", "-y", "-i", str(args.file),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            wav_path
        ])

        # Run mlx-whisper via standalone script
        script_path = str(Path(__file__).parent / "whisper_transcribe.py")
        cmd = [VENV_PYTHON, script_path, wav_path, WHISPER_MODEL]
        if args.language:
            cmd.append(args.language)

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            print(json.dumps({
                "error": "Whisper transcription failed",
                "stderr": proc.stderr[-2000:] if proc.stderr else "",
            }))
            sys.exit(1)

        result = json.loads(proc.stdout)

        if args.summary:
            print(f"Language: {result['language']}")
            print(f"Segments: {len(result['segments'])}")
            print("---")
            for seg in result["segments"]:
                print(f"[{_format_timestamp(seg['start'])} → {_format_timestamp(seg['end'])}] {seg['text']}")
        else:
            print(json.dumps(result, indent=2))

    finally:
        os.unlink(wav_path)


def cmd_scenes(args):
    """Detect scene boundaries using PySceneDetect."""
    scene_script = f"""
import json
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

video = open_video("{args.file}")
scene_manager = SceneManager()
scene_manager.add_detector(ContentDetector(threshold={args.threshold}))
scene_manager.detect_scenes(video)
scene_list = scene_manager.get_scene_list()

scenes = []
for i, (start, end) in enumerate(scene_list):
    scenes.append({{
        "scene": i + 1,
        "start": round(start.get_seconds(), 2),
        "end": round(end.get_seconds(), 2),
        "duration": round((end - start).get_seconds(), 2),
        "start_timecode": str(start),
        "end_timecode": str(end),
    }})

print(json.dumps({{"total_scenes": len(scenes), "scenes": scenes}}))
"""
    out = run_cmd([VENV_PYTHON, "-c", scene_script])
    result = json.loads(out)

    if args.summary:
        print(f"Total scenes: {result['total_scenes']}")
        print("---")
        for s in result["scenes"]:
            print(f"Scene {s['scene']}: {s['start_timecode']} → {s['end_timecode']} ({s['duration']:.1f}s)")
    else:
        print(json.dumps(result, indent=2))


def cmd_describe(args):
    """Describe video content using frame extraction + Ollama LLaVA."""
    # Check ollama is available
    try:
        run_cmd(["ollama", "list"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(json.dumps({"error": "Ollama not available. Install with: brew install ollama && ollama pull llava"}))
        sys.exit(1)

    # Get video duration
    probe = ffprobe_json(args.file)
    duration = float(probe.get("format", {}).get("duration", 0))

    # Calculate frame timestamps
    interval = args.interval
    timestamps = []
    t = 0.0
    while t < duration and len(timestamps) < args.max_frames:
        timestamps.append(t)
        t += interval

    # Extract and describe frames
    descriptions = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, ts in enumerate(timestamps):
            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.jpg")

            # Extract frame
            run_cmd([
                "ffmpeg", "-y", "-ss", str(ts),
                "-i", str(args.file),
                "-vframes", "1", "-q:v", "2",
                frame_path
            ])

            if not os.path.exists(frame_path):
                continue

            # Describe with LLaVA via Ollama API
            try:
                import base64
                with open(frame_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()

                import urllib.request
                req_data = json.dumps({
                    "model": "llava",
                    "prompt": "Describe this image concisely in 2-3 sentences. Focus on: subjects, actions, setting, and mood.",
                    "images": [img_b64],
                    "stream": False,
                }).encode()
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=req_data,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = json.loads(resp.read())
                    description = resp_data.get("response", "").strip()
            except Exception as e:
                description = f"(error: {e})"

            descriptions.append({
                "timestamp": round(ts, 2),
                "timecode": _format_timestamp(ts),
                "description": description,
            })

    output = {
        "file": str(args.file),
        "duration": _format_duration(duration),
        "frames_analyzed": len(descriptions),
        "interval_seconds": interval,
        "descriptions": descriptions,
    }

    if args.summary:
        print(f"Video: {output['file']} ({output['duration']})")
        print(f"Analyzed {output['frames_analyzed']} frames at {interval}s intervals")
        print("---")
        for d in descriptions:
            print(f"[{d['timecode']}] {d['description']}")
    else:
        print(json.dumps(output, indent=2))


# --- Helpers ---

def _format_duration(seconds):
    """Format seconds as HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_size(bytes_val):
    """Format bytes as human-readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def _format_timestamp(seconds):
    """Format seconds as MM:SS or HH:MM:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _parse_fps(fps_str):
    """Parse ffprobe fps fraction string like '30/1'."""
    try:
        num, den = fps_str.split("/")
        return round(int(num) / int(den), 2)
    except (ValueError, ZeroDivisionError):
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Video analysis skill handler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info
    p_info = subparsers.add_parser("info", help="Get video metadata")
    p_info.add_argument("file", type=Path)
    p_info.add_argument("--summary", action="store_true")
    p_info.set_defaults(func=cmd_info)

    # transcribe
    p_trans = subparsers.add_parser("transcribe", help="Transcribe speech")
    p_trans.add_argument("file", type=Path)
    p_trans.add_argument("--language", default=None)
    p_trans.add_argument("--summary", action="store_true")
    p_trans.set_defaults(func=cmd_transcribe)

    # scenes
    p_scenes = subparsers.add_parser("scenes", help="Detect scene boundaries")
    p_scenes.add_argument("file", type=Path)
    p_scenes.add_argument("--threshold", type=float, default=27.0)
    p_scenes.add_argument("--summary", action="store_true")
    p_scenes.set_defaults(func=cmd_scenes)

    # describe
    p_desc = subparsers.add_parser("describe", help="Describe visual content")
    p_desc.add_argument("file", type=Path)
    p_desc.add_argument("--interval", type=int, default=10)
    p_desc.add_argument("--max-frames", type=int, default=10)
    p_desc.add_argument("--summary", action="store_true")
    p_desc.set_defaults(func=cmd_describe)

    args = parser.parse_args()

    # Validate file exists
    if hasattr(args, "file") and not args.file.exists():
        print(json.dumps({"error": f"File not found: {args.file}"}))
        sys.exit(1)

    try:
        args.func(args)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": str(e), "stderr": e.stderr or ""}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
