---
name: video-use
description: >-
  Edit any video by conversation: transcribe, cut, color grade, overlay animations, burn subtitles. Ask questions, confirm the plan, execute, iterate, persist. Use for talking heads, montages, tutorials, interviews.
---

# video-use (pointer)

This is a thin pointer. The real skill is the upstream `browser-use/video-use`
repo, kept outside this repo so `git pull` tracks upstream directly.

## Step 1 — resolve the repo root

The checkout path differs per machine (some checkouts live under `/opt`, others
under `~/opt`), so resolve it, never hardcode it:

```bash
VU=$(ls -d /opt/video-use ~/opt/video-use 2>/dev/null | head -1); echo "$VU"
```

If that prints nothing, the repo is not on this machine. Install it:

```bash
DEST=$([ -w /opt ] && echo /opt/video-use || echo ~/opt/video-use)
git clone https://github.com/browser-use/video-use "$DEST" && cd "$DEST" && uv sync
```

Then read `$VU/install.md` for ffmpeg, yt-dlp and the API key.

## Step 2 — read the real instructions

`$VU/SKILL.md` is the actual skill: the twelve Hard Rules, the directory
layout, the worked examples. Read it before touching any footage. Helpers are
invoked from the repo root, e.g. `cd "$VU" && uv run python helpers/render.py`,
so bare-name references in that file resolve.

## Local notes

- `helpers/timeline_view.py` needs no API and no key. It renders a filmstrip
  plus waveform composite for any range of any video, which is the cheapest way
  to visually QC a render before showing it to a human.
- If `helpers/transcribe.py` (ElevenLabs Scribe) fails with
  `400 api_key_id_used_as_api_key`, your stored key is a key ID, not the `sk_`
  secret — check where you keep it. Everything that does not need a transcript
  still works without it.
- Hard rule 10 (spawn parallel subagents per animation) can burn real API spend
  fast — get an explicit human go-ahead before generating in bulk, regardless
  of what the upstream rule says.
- Hard rules 2, 3, 5, 6 and 7 govern cut-based editing. If your pipeline renders
  one continuous track and never cuts segments, they do not apply to it.
