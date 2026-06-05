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
(`wtf-humanizer`, `wtf-multi-llm-deliberation`, `wtf-visual-qa`, `wtf-premortem`, `wtf-end`, `wtf-idiocy-check`) so they never clash
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

## Contributing

New skills welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Every change is gated
by an automated leak-check that blocks internal hostnames, private paths, and
credentials from ever landing in this public repo.

## License

MIT (see [LICENSE](LICENSE)). Bundled third-party work is attributed in
[NOTICE](NOTICE).
