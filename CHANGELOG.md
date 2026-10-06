# Changelog

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
