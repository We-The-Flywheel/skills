# Flywheel Skills

Reusable [Claude Code](https://code.claude.com) skills maintained by The Flywheel.

This repository is the public distribution mirror of the shared skill pack.
Maintainers develop and review changes in the private shared workspace, then
publish a checked file snapshot here. Installation URLs and skill names stay the
same. Public contributions are welcome through pull requests.

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
- `wtf:multi-llm`
- `wtf:visual-qa`
- `wtf:premortem`
- `wtf:wrapup`
- `wtf:idiocy-check`
- `wtf:release-gate`
- `wtf:content-gate`
- `wtf:og-meta-check`
- `wtf:knowledgepanel`
- `wtf:moodboard`
- `wtf:website-build`
- `wtf:grilling`
- `wtf:skill-test`
- `wtf:verify-claim`
- `wtf:review-feedback`
- `wtf:axi`
- `wtf:debug`
- `wtf:memory-consolidate`
- `wtf:sop`
- `wtf:lavish`
- `wtf:screamingfrog-check`
- `wtf:video-analyze`
- `wtf:video-use`

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
(`wtf-humanizer`, `wtf-multi-llm`, `wtf-visual-qa`, `wtf-premortem`, `wtf-wrapup`, `wtf-idiocy-check`, `wtf-release-gate`, `wtf-content-gate`, `wtf-og-meta-check`, `wtf-moodboard`, `wtf-website-build`, `wtf-grilling`, `wtf-skill-test`, `wtf-verify-claim`, `wtf-review-feedback`, `wtf-knowledgepanel`, `wtf-axi`, `wtf-debug`, `wtf-memory-consolidate`, `wtf-sop`, `wtf-lavish`, `wtf-screamingfrog-check`, `wtf-video-analyze`, `wtf-video-use`) so they never clash
with same-named skills you may already have. Re-running it skips anything already
installed.

## The skills

Grouped by category. (Claude Code discovers plugin skills one level deep, so they live
flat under `plugins/wtf/skills/` — the categories below are organizational, not directories.)

| Category | Skill | What it does | Extra setup |
|----------|-------|--------------|-------------|
| Writing | **humanizer** | Rewrites AI-sounding prose so it reads like the writer, without changing what it says. 31 patterns grouped strongest-first (staging, rhythm by rule, inflation, formatting by rule, drafting leftovers) and severity-ranked, so a single deliberate dash or triad survives while act-on-sight tells do not. Carries a fact guardrail (add no fact absent from the source, drop none present) and three output modes (pasted / file / embedded). Optionally matches a per-project `VOICE.md`. | None |
| Reasoning | **multi-llm** | Runs a 3-stage deliberation (diverge → rank → synthesize) across multiple models via OpenRouter for consensus answers on architecture, code review, or hard questions. Includes a Content Truth-Check Mode that fact-checks draft articles: atomic claim extraction → cross-model verdicts (disagreement = hallucination flag) → web verification of volatile/disputed claims → surgical fixes. | `OPENROUTER_API_KEY` (or a gateway URL + `MULTILLM_GATEWAY_TOKEN`) in your environment or `~/.env.shared` |
| QA | **visual-qa** | Captures full-page screenshots of a site at desktop/tablet/mobile widths and renders them into one tabbed HTML gallery for visual review. | Node.js; runs `npm install` (Playwright) on first use via `setup.sh` |
| Decisions | **premortem** | Stress-tests a plan before you commit: imagines it's failed months from now, spawns one investigator per failure mode in parallel, then synthesizes the most likely / most dangerous failure, the biggest hidden assumption, a revised plan, and a pre-commit checklist. | None |
| Workflow | **wrapup** | Wraps up a coding session: shuts down local dev servers, removes temp/backup files, commits and pushes outstanding work, and refreshes project docs (PROJECT_MAP.md + CLAUDE.md). Safe-by-default — confirms before anything destructive. | None |
| Writing | **idiocy-check** | Fast, ruthless pre-submission review of any document, grant, caption, email, or deliverable. Returns 5–8 items that would embarrass you, get you rejected, or make you look sloppy — not a comprehensive edit. Contributed by Eric Cross. | None |
| QA | **release-gate** | Evidence-based ship gate for larger implementations: deterministic gates (secrets scan, build, lint, tests, coverage delta), rubric'd pass/fail dimension checks with adversarial verification of every finding, and runtime evidence (run the app, observe). Emits a PASS/FAIL report card. Read-only — never edits. Supports a per-project `VERIFY_RUBRIC.md`. | None |
| QA | **content-gate** | Ten-step pre-publish gate for web content (blog posts, landing pages, SEO articles): draft quality + voice profile, fact-check, de-AI pass, hero/OG image, full OG/Twitter meta, FAQ + `FAQPage` JSON-LD, schema + E-E-A-T signals, analytics coverage,, AI-citation/zero-click readiness (self-contained answer above the fold — ~60% of searches end without a click), and Google's Preferred Sources button in the post template. Emits a per-step PASS/FAIL report card; any FAIL blocks publish. Pairs with `wtf:humanizer` (Step 3), `wtf:multi-llm` Truth-Check Mode (Step 2), and delegates Step 5 to `wtf:og-meta-check`. | None |
| QA | **og-meta-check** | Standalone check that a page emits the full Open Graph + Twitter Card meta-tag set (site_name, title/description, absolute image URLs, `twitter:card=summary_large_image`, canonical, …) — the tags that control link-preview cards on iMessage, Slack, WhatsApp, X, and LinkedIn. PASS/FAIL with the missing-tag list. Extracted from `wtf:content-gate` Step 5 so it can run on its own. | None |
| SEO | **knowledgepanel** | Audit and build Google Knowledge Panel / entity setup for a person or brand: the Entity Home rule (your About page, not your homepage), the `sameAs` corroboration loop, the JSON-LD identity node and its permanent `@id`, KGMID lookup via the Google Knowledge Graph Search API, and the 150-word executive summary that feeds Crunchbase, LinkedIn and your schema alike. Emits a 14-row PASS/FAIL report card; structural failures block the rest. | `GOOGLE_API_KEY` (free) for KGMID lookup; `DATAFORSEO_*` optional for rendered-panel checks |
| Design | **moodboard** | Turns visual references (and anti-references) into locked design decisions — background, type category, accent approach, nav scale, interaction patterns, anti-patterns — each traceable to a finding. Includes an in-context type explorer (renders the real wordmark in 8–12 fonts on the actual brand background, one scroll). Produces documented decisions, not pages. | None |
| Design | **riff** | Divergent design ideation for the *start* of design work: generates 3–5 deliberately far-apart, fully-rendered directions (forced family diversity, at least one wildcard, real copy — never wireframes) as standalone HTML files in one tabbed compare artifact with viewport toggles, then a pick-and-lock step that writes the winning thesis, exact fonts, colour strategy and anti-decisions to `LOCKED-DIRECTION.md` for `wtf:moodboard` to convert into tokens. Deliberately ignores any existing design system — divergence under enforcement just yields four shades of the same idea. | None |
| Design | **website-build** | Reference-first site build on a four-pillars framework (Audience → Structure → Copy → Design): clarity-paragraph gate, audience filter, four-visitor-jobs structure with an accountability map for every cut, voice spec, and a Design pillar handed to `wtf:moodboard`. Produces a populated brief; blanks are the to-do list. Pairs with `wtf:humanizer` and `wtf:content-gate` when installed. | None |
| Decisions | **grilling** | Interviews the user relentlessly about a plan, decision, or idea until reaching shared understanding — maps the decision as a tree, works the frontier in numbered rounds with recommended answers, and won't move on until every branch is settled. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Writing | **skill-test** | TDD applied to process documentation: write pressure scenarios, watch an agent fail without the skill (RED), write the skill (GREEN), close loopholes (REFACTOR). Covers SKILL.md structure, discovery optimization, flowchart usage, and wording micro-tests against a no-guidance control before running full pressure scenarios. Use when authoring or editing a skill and testing whether its guidance actually holds under pressure — not a general writing-for-agents reference. Adopted (renamed from upstream `writing-skills`, then again locally) from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |
| QA | **verify-claim** | Discipline for claiming work is done: run the actual verification commands and read their output before saying "fixed", "passing", or "complete" — evidence before assertions, always. A lightweight per-claim reflex; pairs with `wtf:release-gate`'s full evidence-gate ceremony on larger diffs. Adopted (renamed from upstream `verification-before-completion`, then again locally) from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |
| Workflow | **review-feedback** | Discipline for handling code review feedback: verify before implementing, ask before assuming, push back with technical reasoning instead of performative agreement, and grep-check YAGNI before building "proper" versions of unused features. Adopted (renamed from upstream `receiving-code-review`) from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |
| Workflow | **mission** | Multi-agent build mode modeled on Factory AI's Missions (Luke Alvoeiro, "The Multi-Agent Architecture That Actually Ships"): the orchestrator plans with you and writes a validation contract of countable assertions before any code, fresh-context workers build one feature at a time, and separate scrutiny (lint, types, tests, code review) and user-testing (drives the real app) validators check each milestone. Unsatisfied assertions become follow-up features; every role transition leaves a structured handoff in `.mission/`. Replaces the former `autopilot` skill, which was merged into it. | None |
| Engineering | **improve-codebase-architecture** | Finds deepening opportunities in a codebase (shallow modules, leaky seams) and walks you through one with `wtf:grilling`, keeping the domain model current as decisions land. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Engineering | **codebase-design** | Shared vocabulary for designing deep modules: module, interface, depth, seam, adapter, leverage, locality, plus the deletion test and a design-it-twice pattern. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Engineering | **tdd** | Test-driven development with red-green-refactor and integration tests, including guidance on what to mock. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Engineering | **domain-modeling** | Builds and sharpens a project's domain model: GLOSSARY.md terms and ADRs. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Engineering | **axi** | Agent eXperience Interface: ergonomic standards for building CLI tools that agents use via shell execution — token-efficient output (TOON), minimal default schemas, structured errors, ambient context via session hooks, and a fast `--version` path. Use when building, modifying, or reviewing any agent-facing CLI. | None |
| Debugging | **debug** | Four-phase debugging framework — root cause investigation, pattern analysis, hypothesis testing, implementation — with an Iron Law against fixing symptoms before understanding the cause. Use on any bug, test failure, or unexpected behavior before proposing a fix. | None |
| Ops | **memory-consolidate** | Reviews Claude Code's per-project memory files, verifies code-specific claims still hold (file paths, function names, config flags), removes stale entries, merges duplicates, and drafts new skill candidates from repeated patterns. | None |
| Content | **sop** | Creates, edits, or reviews Standard Operating Procedures with one consistent structure (phases, verification, rollback) across projects. | None |
| Productivity | **lavish** | Turns a plan, comparison, diagram, table, diff, or report into a rich, annotatable HTML artifact opened in the browser via the `lavish-axi` CLI, so a human can mark it up and send feedback back to the agent. | Node.js (`npx`) |
| QA | **screamingfrog-check** | Headless Screaming Frog crawl for SEO and technical issues, extended with the checks SF's default exports miss (structured data, OG/Twitter tags, robots/sitemap health, accessibility, performance) and a prioritized fix plan. | Screaming Frog SEO Spider CLI |
| Media | **video-analyze** | Analyzes video files without loading binary data into context: metadata (ffprobe), transcription (mlx-whisper), scene detection (PySceneDetect), and visual description of key frames (Ollama/LLaVA). | ffmpeg, ollama; `setup.sh` for the rest |
| Media | **video-use** | Thin pointer to the upstream [browser-use/video-use](https://github.com/browser-use/video-use) skill for conversational video editing: transcribe, cut, color grade, overlay animations, burn subtitles. | Clones the upstream repo on first use |

**Commands and agents (Research, Plan, Implement).** The plugin also ships HumanLayer's RPI workflow as slash commands: `/wtf:research_codebase` documents the code as it is into `docs/research/`, `/wtf:create_plan` writes a phased plan to `docs/plans/`, `/wtf:iterate_plan` revises it, `/wtf:implement_plan` executes it phase by phase, and `/wtf:validate_plan` checks the result against the plan's success criteria. They use three read-only subagents: `codebase-locator`, `codebase-analyzer` and `codebase-pattern-finder`. Adopted from [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) (Apache-2.0). Plugin install only: `scripts/install.sh` copies skills, not commands or agents.

## When to use what — the lifecycle

The skills are designed to slot into the phases of a normal product loop. You don't
need all of them on every change — match the phase you're in:

```
PLAN ──────────► BUILD ──────────► CHECK ──────────► SHIP ──────────► REFLECT
premortem        (Claude Code      code review*      release-gate     retro habits
multi-llm        plan mode,        visual-qa         content-gate     (what failed →
                 tests as          humanizer         end              new rubric line
                 you go)           idiocy-check                       or skill)
```

- **PLAN** — before committing to an approach: `wtf:premortem` stress-tests the plan
  (how does this fail?); `wtf:multi-llm` settles architecture calls when
  there are >2 defensible approaches.
  For *design* work specifically, the order is **diverge → lock → enforce**: `wtf:riff`
  generates the option space when no design system is chosen yet, and the winner locks
  via `wtf:moodboard` into tokens your build then conforms to.
- **BUILD** — mostly Claude Code itself: plan mode, tests alongside code.
- **CHECK** — two distinct steps, in order:
  1. *Code review* (judgment — Claude Code's built-in `/code-review`*): findings,
     opinions, suggestions. "Is this good code?"
  2. `wtf:release-gate` (evidence — this pack): binary gates with proof. "Does this meet
     the bar to ship?" Review advises; the gate gatekeeps.
  Plus `wtf:visual-qa` for anything with a UI, and `wtf:humanizer` /
  `wtf:idiocy-check` for prose and deliverables.
- **SHIP** — `wtf:release-gate` must be green first; for anything going to a public URL
  (blog posts, landing pages, SEO articles), `wtf:content-gate` must also be green —
  it's the content counterpart to the release gate (meta tags, FAQ + structured data,
  E-E-A-T, analytics, zero-click/AI-citation readiness). Then commit/push/deploy and
  close the session with `wtf:wrapup`.
- **REFLECT** — when the gate or review caught something late, encode it: add a line to
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
