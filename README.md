# Flywheel Skills

Reusable [Claude Code](https://code.claude.com) skills maintained by The Flywheel.

Distributed as a Claude Code **plugin marketplace** so you can install everything
with two commands — no manual file copying.

## Install (recommended — plugin marketplace)

In any Claude Code session:

```
/plugin marketplace add We-The-Flywheel/skills
/plugin install wtf@flywheel
```

That's it. The skills are now available, namespaced under `wtf:`:

- `wtf:humanizer`
- `wtf:multi-llm-deliberation`
- `wtf:visual-qa`
- `wtf:premortem`
- `wtf:end`
- `wtf:idiocy-check`
- `wtf:verify`

To update later: `/plugin marketplace update flywheel`.

## Install (alternative — clone + script)

If you'd rather not use the marketplace (older Claude Code, or you just prefer
cloning):

```bash
git clone https://github.com/We-The-Flywheel/skills.git
cd skills
./scripts/install.sh
```

`install.sh` copies each skill into `~/.claude/skills/` with a `wtf-` prefix
(`wtf-humanizer`, `wtf-multi-llm-deliberation`, `wtf-visual-qa`, `wtf-premortem`, `wtf-end`, `wtf-idiocy-check`, `wtf-verify`) so they never clash
with same-named skills you may already have. Re-running it skips anything already
installed.

## The skills

Grouped by category. (Claude Code discovers plugin skills one level deep, so they live
flat under `plugins/wtf/skills/` — the categories below are organizational, not directories.)

| Category | Skill | What it does | Extra setup |
|----------|-------|--------------|-------------|
| Writing | **humanizer** | Strips the tells of AI-generated writing (em-dash overuse, rule-of-three, inflated symbolism, vague attributions, …). Optionally matches a per-project `VOICE.md`. | None |
| Reasoning | **multi-llm-deliberation** | Runs a 3-stage deliberation (diverge → rank → synthesize) across multiple models via OpenRouter for consensus answers on architecture, code review, or hard questions. Includes a Content Truth-Check Mode that fact-checks draft articles: atomic claim extraction → cross-model verdicts (disagreement = hallucination flag) → web verification of volatile/disputed claims → surgical fixes. | `OPENROUTER_API_KEY` in your environment or `~/.env.shared` |
| QA | **visual-qa** | Captures full-page screenshots of a site at desktop/tablet/mobile widths and renders them into one tabbed HTML gallery for visual review. | Node.js; runs `npm install` (Playwright) on first use via `setup.sh` |
| Decisions | **premortem** | Stress-tests a plan before you commit: imagines it's failed months from now, spawns one investigator per failure mode in parallel, then synthesizes the most likely / most dangerous failure, the biggest hidden assumption, a revised plan, and a pre-commit checklist. | None |
| Workflow | **end** | Wraps up a coding session: shuts down local dev servers, removes temp/backup files, commits and pushes outstanding work, and refreshes project docs (PROJECT_MAP.md + CLAUDE.md). Safe-by-default — confirms before anything destructive. | None |
| Writing | **idiocy-check** | Fast, ruthless pre-submission review of any document, grant, caption, email, or deliverable. Returns 5–8 items that would embarrass you, get you rejected, or make you look sloppy — not a comprehensive edit. Contributed by Eric Cross. | None |
| QA | **verify** | Evidence-based ship gate for larger implementations: deterministic gates (secrets scan, build, lint, tests, coverage delta), rubric'd pass/fail dimension checks with adversarial verification of every finding, and runtime evidence (run the app, observe). Emits a PASS/FAIL report card. Read-only — never edits. Supports a per-project `VERIFY_RUBRIC.md`. | None |

## When to use what — the lifecycle

The skills are designed to slot into the phases of a normal product loop. You don't
need all of them on every change — match the phase you're in:

```
PLAN ──────────► BUILD ──────────► CHECK ──────────► SHIP ──────────► REFLECT
premortem        (Claude Code      code review*      verify           retro habits
multi-llm-       plan mode,        visual-qa         end              (what failed →
deliberation     tests as          humanizer                          new rubric line
                 you go)           idiocy-check                       or skill)
```

- **PLAN** — before committing to an approach: `wtf:premortem` stress-tests the plan
  (how does this fail?); `wtf:multi-llm-deliberation` settles architecture calls when
  there are >2 defensible approaches.
- **BUILD** — mostly Claude Code itself: plan mode, tests alongside code.
- **CHECK** — two distinct steps, in order:
  1. *Code review* (judgment — Claude Code's built-in `/code-review`*): findings,
     opinions, suggestions. "Is this good code?"
  2. `wtf:verify` (evidence — this pack): binary gates with proof. "Does this meet
     the bar to ship?" Review advises; verify gatekeeps.
  Plus `wtf:visual-qa` for anything with a UI, and `wtf:humanizer` /
  `wtf:idiocy-check` for prose and deliverables.
- **SHIP** — `wtf:verify` must be green first; then commit/push/deploy and close the
  session with `wtf:end`.
- **REFLECT** — when verify or review caught something late, encode it: add a line to
  your `VERIFY_RUBRIC.md` so the gate catches it automatically next time.

\* `/code-review` is built into Claude Code, not part of this pack — listed for the
sequence's sake.

## Contributing

New skills welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Every change is gated
by an automated leak-check that blocks internal hostnames, private paths, and
credentials from ever landing in this public repo.

## License

MIT (see [LICENSE](LICENSE)). Bundled third-party work is attributed in
[NOTICE](NOTICE).
