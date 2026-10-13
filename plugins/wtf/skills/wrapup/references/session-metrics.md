# Step 8: session metrics

Moved verbatim from `SKILL.md`; read at the step that points here.

Append a structured JSONL entry to `.session-metrics.jsonl` in the project root — input for periodic retrospectives and cross-session pattern analysis (which agent types succeed, what escalation patterns recur, where QC catches real issues vs false positives).

```json
{
  "date": "YYYY-MM-DDTHH:MM:SS",
  "branch": "[current branch]",
  "duration_min": "[estimated from first to last commit, or conversation length]",
  "commits": "[N this session]",
  "files_changed": "[N]",
  "agents_spawned": [{"type": "code-reviewer", "outcome": "pass", "model": "sonnet"}],
  "escalations": {"count": 0, "categories": [], "correct": 0, "missed": 0},
  "qc_verdicts": {"pass": 0, "flag": 0, "block": 0},
  "sweep_candidates": 0,
  "skills_used": ["go-live", "debug"],
  "model": "[primary model used]"
}
```

```bash
echo '{...}' >> .session-metrics.jsonl
```

**Rules:** append-only — never overwrite or truncate; add `.session-metrics.jsonl` to `.gitignore` if not already there (local analytics, not committed); if no agents/escalations occurred, still log the basic metrics — absence is itself a data point.
