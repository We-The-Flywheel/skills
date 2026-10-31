# Changelog

## 0.37.1 — Learn from interactions and mistakes

- Wrapup reviews user corrections and agent errors, including short interactions, and saves concrete prevention guidance with evidence in an authorized durable location.

## 0.37.0 — Approved skill names and combined website grounding

- Rename videoedit, architectureaudit and idiocycheck; combine site brief and charter/KPI grounding as websitegrounding. Preserve explicit legacy shortcuts.

## 0.36.2 — Restore multillm

- Restore `wtf:multillm` as the canonical command. Keep `wtf:multi-llm` as an explicit-only compatibility shortcut; clone upgrades back up the old implementation.

## [0.36.1] - 2026-10-20

- Rename the explicit `grill-me` shortcut to `grillme`; keep `grilling` as the automatic skill. Clone installs archive the previous alias.

## 0.36.0 - 2026-10-13

- Shorter descriptions for 12 skills (riff, mission, content-gate, premortem, moodboard, release-gate, knowledgepanel, og-meta-check, multi-llm, idiocy-check, humanizer, wrapup). The skill listing loads into every session, so this cuts a fixed cost.
- humanizer: SKILL.md drops from 46 KB to 22 KB. Before/after examples and the full text of the lower-tier patterns move verbatim into `references/`, and the body points to the file to read for each group.
- wrapup: SKILL.md drops from 36 KB to 23 KB. Templates and conditional steps (handoff and decision templates, memory health, project-map formats, metrics, error handling, manual mode) move verbatim into `references/`. Steps that run every time stay inline.

## 0.35.1 - 2026-10-10

- Make `grill-me` and `end` explicit shortcuts, leaving automatic selection to `grilling` and `wrapup`. Both aliases work in harnesses without a Skill tool; clone installs refresh old aliases with a backup.
- Move retired `diagnose` and `writing-for-agents` sources outside plugin discovery while preserving attribution. The clone installer archives their legacy copies and the former `skill-writing` name.

## 0.35.0 - 2026-10-06

- grilling gains an open-questions mode: it collects the questions and decisions already waiting on the user (thread, session handoff, design docs) and asks them. It replaces the separate internal `questions` skill.
- grilling asks choice-shaped questions through an interactive picker (Claude Code's `AskUserQuestion`) when one exists, in batches of 4, and records the answers.
- Add `grill-me` as an alias for grilling, matching the upstream name in mattpocock/skills.

## 0.34.0 - 2026-10-05

- Require wrapup to verify commits, the selected remote base, and deployment before reporting completion.
- Verify local and remote deletion of merged topic branches and completed temporary worktrees, including squash merges and earlier session merges. Preserve active work and report blocked cleanup.
- Scope commits to authorized session changes in shared checkouts. The end alias inherits these checks.

## 0.33.0 - 2026-10-05

- Link content-gate's warning-only internal-link coverage check to the internal-linking workflow, preserve existing PASS/FAIL checks, and report unavailable proposal workflows accurately.
- Clarify that eligible pilot links are approved autonomously and still pass through the normal build and pull-request lane.

## [2026-10-02] - Public distribution mirror
### Changed
- Documented the shared development and reviewed publication workflow. Existing marketplace URLs, skill names, and package version remain unchanged.
### Fixed
- The public leak check now handles Git worktree metadata while continuing to scan repository content.

## 0.32.0 - 2026-10-04

- Add `end` as an alias for `wrapup`, so `/end` (or `wtf:end`) closes a session
  the same way.

## 0.31.0 - 2026-10-01

- Let organisations add private closure, drift and documentation checks to
  `wrapup` through the existing house-overlay mechanism.

## 0.30.0 - 2026-10-01

- Reversibly archive pangram, ultrahumanizer and longterm outside active discovery.
- Clarify website-build discovery and the brief, disposable POC, design and
  editorial scaffold handoffs.
