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
- `wtf:multillm` (alias: `wtf:multi-llm-deliberation`)
- `wtf:visual-qa`
- `wtf:premortem`
- `wtf:end`
- `wtf:idiocy-check`
- `wtf:release-gate`
- `wtf:content-gate`
- `wtf:og-meta-check`
- `wtf:knowledgepanel`
- `wtf:moodboard`
- `wtf:website-build`
- `wtf:longterm`
- `wtf:pangram`
- `wtf:ultrahumanizer`
- `wtf:diagnosing-bugs`
- `wtf:grilling`
- `wtf:skill-writing`
- `wtf:verification`
- `wtf:receiving-code-review`

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
(`wtf-humanizer`, `wtf-multillm`, `wtf-visual-qa`, `wtf-premortem`, `wtf-end`, `wtf-idiocy-check`, `wtf-release-gate`, `wtf-content-gate`, `wtf-og-meta-check`, `wtf-moodboard`, `wtf-website-build`, `wtf-longterm`, `wtf-pangram`, `wtf-ultrahumanizer`, `wtf-diagnosing-bugs`, `wtf-grilling`, `wtf-skill-writing`, `wtf-verification`, `wtf-receiving-code-review`, `wtf-knowledgepanel`) so they never clash
with same-named skills you may already have. Re-running it skips anything already
installed.

## The skills

Grouped by category. (Claude Code discovers plugin skills one level deep, so they live
flat under `plugins/wtf/skills/` — the categories below are organizational, not directories.)

| Category | Skill | What it does | Extra setup |
|----------|-------|--------------|-------------|
| Writing | **humanizer** | Rewrites AI-sounding prose so it reads like the writer, without changing what it says. 31 patterns grouped strongest-first (staging, rhythm by rule, inflation, formatting by rule, drafting leftovers) and severity-ranked, so a single deliberate dash or triad survives while act-on-sight tells do not. Carries a fact guardrail (add no fact absent from the source, drop none present) and three output modes (pasted / file / embedded). Optionally matches a per-project `VOICE.md`. | None |
| Reasoning | **multillm** | Runs a 3-stage deliberation (diverge → rank → synthesize) across multiple models via OpenRouter for consensus answers on architecture, code review, or hard questions. Includes a Content Truth-Check Mode that fact-checks draft articles: atomic claim extraction → cross-model verdicts (disagreement = hallucination flag) → web verification of volatile/disputed claims → surgical fixes. | `OPENROUTER_API_KEY` in your environment or `~/.env.shared` |
| QA | **visual-qa** | Captures full-page screenshots of a site at desktop/tablet/mobile widths and renders them into one tabbed HTML gallery for visual review. | Node.js; runs `npm install` (Playwright) on first use via `setup.sh` |
| Decisions | **premortem** | Stress-tests a plan before you commit: imagines it's failed months from now, spawns one investigator per failure mode in parallel, then synthesizes the most likely / most dangerous failure, the biggest hidden assumption, a revised plan, and a pre-commit checklist. | None |
| Workflow | **end** | Wraps up a coding session: shuts down local dev servers, removes temp/backup files, commits and pushes outstanding work, and refreshes project docs (PROJECT_MAP.md + CLAUDE.md). Safe-by-default — confirms before anything destructive. | None |
| Writing | **idiocy-check** | Fast, ruthless pre-submission review of any document, grant, caption, email, or deliverable. Returns 5–8 items that would embarrass you, get you rejected, or make you look sloppy — not a comprehensive edit. Contributed by Eric Cross. | None |
| QA | **release-gate** | Evidence-based ship gate for larger implementations: deterministic gates (secrets scan, build, lint, tests, coverage delta), rubric'd pass/fail dimension checks with adversarial verification of every finding, and runtime evidence (run the app, observe). Emits a PASS/FAIL report card. Read-only — never edits. Supports a per-project `VERIFY_RUBRIC.md`. | None |
| QA | **content-gate** | Nine-step pre-publish gate for web content (blog posts, landing pages, SEO articles): draft quality + voice profile, fact-check, de-AI pass, hero/OG image, full OG/Twitter meta, FAQ + `FAQPage` JSON-LD, schema + E-E-A-T signals, analytics coverage, and AI-citation/zero-click readiness (self-contained answer above the fold — ~60% of searches end without a click). Emits a per-step PASS/FAIL report card; any FAIL blocks publish. Pairs with `wtf:humanizer` (Step 3), `wtf:multillm` Truth-Check Mode (Step 2), and delegates Step 5 to `wtf:og-meta-check`. | None |
| QA | **og-meta-check** | Standalone check that a page emits the full Open Graph + Twitter Card meta-tag set (site_name, title/description, absolute image URLs, `twitter:card=summary_large_image`, canonical, …) — the tags that control link-preview cards on iMessage, Slack, WhatsApp, X, and LinkedIn. PASS/FAIL with the missing-tag list. Extracted from `wtf:content-gate` Step 5 so it can run on its own. | None |
| SEO | **knowledgepanel** | Audit and build Google Knowledge Panel / entity setup for a person or brand: the Entity Home rule (your About page, not your homepage), the `sameAs` corroboration loop, the JSON-LD identity node and its permanent `@id`, KGMID lookup via the Google Knowledge Graph Search API, and the 150-word executive summary that feeds Crunchbase, LinkedIn and your schema alike. Emits a 14-row PASS/FAIL report card; structural failures block the rest. | `GOOGLE_API_KEY` (free) for KGMID lookup; `DATAFORSEO_*` optional for rendered-panel checks |
| Design | **moodboard** | Turns visual references (and anti-references) into locked design decisions — background, type category, accent approach, nav scale, interaction patterns, anti-patterns — each traceable to a finding. Includes an in-context type explorer (renders the real wordmark in 8–12 fonts on the actual brand background, one scroll). Produces documented decisions, not pages. | None |
| Design | **riff** | Divergent design ideation for the *start* of design work: generates 3–5 deliberately far-apart, fully-rendered directions (forced family diversity, at least one wildcard, real copy — never wireframes) as standalone HTML files in one tabbed compare artifact with viewport toggles, then a pick-and-lock step that writes the winning thesis, exact fonts, colour strategy and anti-decisions to `LOCKED-DIRECTION.md` for `wtf:moodboard` to convert into tokens. Deliberately ignores any existing design system — divergence under enforcement just yields four shades of the same idea. | None |
| Design | **website-build** | Reference-first site build on a four-pillars framework (Audience → Structure → Copy → Design): clarity-paragraph gate, audience filter, four-visitor-jobs structure with an accountability map for every cut, voice spec, and a Design pillar handed to `wtf:moodboard`. Produces a populated brief; blanks are the to-do list. Pairs with `wtf:humanizer` and `wtf:content-gate` when installed. | None |
| Decisions | **longterm** | When several approaches are on the table, picks and proceeds with the one that's correct for the long term — scoring each on root-cause correctness, maintainability, robustness, reversibility, and total cost over time, accepting more effort now to avoid compounding debt. Guards against over-engineering and stops to confirm on auth/schema/billing/infra/security choices. | None |
| QA | **pangram** | Scores text for AI-generated content via the Pangram Labs API — returns overall AI fraction (0–100%), prediction label, and per-sentence highlights, with a cost estimate per call. Standalone QA tool, not a publishing gate step: the score reflects how text was produced, and editing AI-origin text does not move it. | `PANGRAM_API_KEY` in your environment |
| Writing | **ultrahumanizer** | Human-in-the-loop loop to a passing Pangram verdict: scores the draft, maps flagged ~380-word windows back to passages, reduces them to content bullets, and coaches the *human* to rewrite those passages in their own words — then re-scores until pass or honest stall. The agent never regenerates flagged prose itself (empirically, agent rewrites don't move Pangram). Builds on `wtf:humanizer` + `wtf:pangram`. | `PANGRAM_API_KEY` in your environment |
| Debugging | **diagnosing-bugs** | Discipline for hard bugs and performance regressions: redact-first artifact capture, phase-gated diagnosis loop, and an optional human-in-the-loop script (`scripts/hitl-loop.template.sh`) for iterating with a human in the loop. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Decisions | **grilling** | Interviews the user relentlessly about a plan, decision, or idea until reaching shared understanding — maps the decision as a tree, works the frontier in numbered rounds with recommended answers, and won't move on until every branch is settled. Adopted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). | None |
| Writing | **skill-writing** | TDD applied to process documentation: write pressure scenarios, watch an agent fail without the skill (RED), write the skill (GREEN), close loopholes (REFACTOR). Covers SKILL.md structure, discovery optimization, flowchart usage, and wording micro-tests against a no-guidance control before running full pressure scenarios. Use when authoring or editing a skill and testing whether its guidance actually holds under pressure — not a general writing-for-agents reference. Adopted (renamed from upstream `writing-skills`) from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |
| QA | **verification** | Discipline for claiming work is done: run the actual verification commands and read their output before saying "fixed", "passing", or "complete" — evidence before assertions, always. A lightweight per-claim reflex; pairs with `wtf:release-gate`'s full evidence-gate ceremony on larger diffs. Adopted (renamed from upstream `verification-before-completion`) from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |
| Workflow | **receiving-code-review** | Discipline for handling code review feedback: verify before implementing, ask before assuming, push back with technical reasoning instead of performative agreement, and grep-check YAGNI before building "proper" versions of unused features. Adopted from [obra/superpowers](https://github.com/obra/superpowers) (MIT). | None |

## When to use what — the lifecycle

The skills are designed to slot into the phases of a normal product loop. You don't
need all of them on every change — match the phase you're in:

```
PLAN ──────────► BUILD ──────────► CHECK ──────────► SHIP ──────────► REFLECT
premortem        (Claude Code      code review*      release-gate     retro habits
multi-llm-       plan mode,        visual-qa         content-gate     (what failed →
deliberation     tests as          humanizer         end              new rubric line
                 you go)           idiocy-check                       or skill)
```

- **PLAN** — before committing to an approach: `wtf:premortem` stress-tests the plan
  (how does this fail?); `wtf:multillm` settles architecture calls when
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
  close the session with `wtf:end`.
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
