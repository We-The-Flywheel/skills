---
name: websitegrounding
description: >-
  Establish or update a website's brand, voice, audience, strategy, monetization,
  KPIs and reference brief, then hand off for design and implementation. Use for
  grounding a site, planning a website, defining its ICP or KPIs. On existing sites,
  preserve reviewed work and update only requested, missing or stale parts.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - Skill
  - WebFetch
uses:
  - skill: moodboard
    relation: delegates
    why: Lock the approved design direction
  - skill: humanizer
    relation: requires
    why: Edit drafted site copy for the owner's voice
  - skill: riff
    relation: delegates
    why: Explore distinct design directions when needed
department: design
---

# Website grounding

Produce a coherent site foundation and a usable reference brief before building
pages. For an existing site or a named phase, update only the requested scope;
KPI work alone does not require a redesign. Do not invent facts or fill unknowns
with confident guesses. State unresolved decisions and who can resolve them.

**Local overlay.** If `~/.local/share/flywheel/house/websitegrounding.md` exists,
read it before starting, unless the user explicitly requests the generic workflow
without this optional overlay. Project instructions still apply. It supplies the organisation's file contracts, taxonomy,
KPI systems, validation and publishing procedure. Apply its rules at the matching
phases below; run each phase once. It takes precedence over these generic defaults
without expanding the user's authorization. Without an overlay, this workflow
still runs using the project's existing sources and tools.

## 1. Inventory and scope

Read the project's instructions and its linked audience, brand, voice, strategy,
monetization, KPI and design sources. Inventory each artifact as reviewed, draft,
missing or stale; cite the evidence and validator result when available. Reuse
existing filenames/contracts rather than creating a second source of truth.

Preserve reviewed material. For a new site, fill the missing foundation and brief.
For an existing site, run only requested phases or missing/stale dependencies
needed for the requested result. Leave valid unrelated drafts alone. If existing
sources conflict, show the conflict before choosing a new position.

Write the clarity paragraph: what the site is, whom it serves, and why it exists.
If that cannot be stated plainly, resolve that uncertainty before page building.

## 2. Evidence, brand, voice and strategy

Use existing content, research and measured traffic where available. For a new
positioning or audience decision, inspect the existing content coverage and a
bounded set of relevant competitors; record sources, dates and gaps. Distinguish
assumptions, research and measured evidence. Absence of analytics is not zero
traffic and is not permission to invent measurements.

Capture the brand promise, supported claims, voice, mission, positioning,
audience jobs and exclusions, strategic bets and horizon. Ask only for decisions
or firsthand facts the sources cannot establish. Reuse the owner's language and
voice samples. Never fabricate experience, credentials or results. New material
stays draft until its actual reviewer approves it; do not mark it reviewed.

Map each audience to the problem it needs the site to solve. Optional demographic
or firmographic fields can remain absent. Record the evidence behind each choice.

## 3. Monetization and KPIs

Record intended revenue mechanisms and their evidence. Separate an idea, a planned
mechanism, a published program and a verified relationship. Do not invent partner
terms, payout values or approvals. Link each active revenue mechanism to the KPI
that would show it working.

Use the project's authoritative KPI catalog/template and measurement system when
present. For each KPI record its definition, unit, source, cadence and owner;
select a primary metric tied to the site's purpose. Inspect which events are
actually emitted and mark measurement gaps explicitly. Separate observed
baselines from targets. Obtain target numbers from the owner or an approved
source, never manufacture them.

If the project has a managed KPI system, follow the overlay/project's documented
setup and approval procedure; preview the proposed row changes, obtain required
approval, apply through the supported tool and verify readback. A draft KPI.md
alone is not evidence that tracking or catalog rows are configured. If setup
cannot be completed, keep the relevant output draft and report the blocker.
Without a managed system, record the definitions and proposed instrumentation
plan locally and say what remains unconfigured.

## 4. Reference brief: audience, structure, copy, design

Read [reference-brief.md](references/reference-brief.md) when creating or updating
the site brief. This preserves the four-pillar workflow in detail. Reuse the
foundation above rather than asking the same questions twice. Populate a live
brief such as REFERENCE.md, preserving existing project conventions, with:

- Audience and visitor jobs, linked to the grounding sources.
- Page structure and a reason for each page; account for navigation items removed
  or moved elsewhere.
- Copy: naming, loglines, voice, language to use/avoid, supported claims.
- Design references and anti-references, with decisions still awaiting approval.

Link strategic bets and KPIs from the brief; do not copy the KPI registry into a
second competing table. Leave genuine unknowns blank with an owner/action.
Keep the build log separate from the brief. Edit drafted copy with humanizer
when available; public publication still follows the project's content gate.

## 5. Validate and hand off

Run the project's actual validators for changed artifacts and their dependencies.
Report separately: drafted files, approved choices, configured measurement,
remaining decisions, and verification results. Preserve draft/review labels.
For a named partial phase, stop once that phase and necessary dependencies are
complete; do not launch unrelated design or infrastructure work.

For a new design that needs options, use riff if installed, get the direction
chosen, then lock it through moodboard. Build through the project's production
UI/design-system workflow. If specialized site scaffolding is available, pass it
the approved foundation and brief; grounding itself does not provision domains
or authorize a public launch. For an unproven product claim, use the installed
prototype workflow before production implementation.

Commit/publish only within the request and project rules. A completed brief is
not a built website; configured KPI rows are not proof that events arrived.
