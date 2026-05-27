# Contributing a skill

This is a **public** repo. The #1 rule: **nothing confidential ever lands here** —
no internal hostnames, private paths, credentials, personal emails, or
business-specific domains. An automated leak-check (`scripts/scrub-check.sh`, also
run in CI) enforces this, but you are the first line of defense.

## Add a skill in 4 steps

1. **Create the skill folder** under `plugins/fw/skills/<your-skill>/` with a
   `SKILL.md`. The `name:` in its frontmatter must match the folder name and stay
   **unprefixed** (e.g. `name: my-skill`). The `fw:` prefix is supplied
   automatically by the plugin — don't bake it into the name.

2. **Scrub it.** Before committing, remove anything machine- or business-specific:
   - internal machine hostnames and `*.local` addresses
   - absolute home paths and private infrastructure paths (anything under `/opt/...`
     that belongs to our internal tooling, or a hard-coded `/Users/<you>/...`)
   - credentials / credential files (hard-code nothing; the only allowed env-file
     reference is the literal token `~/.env.shared`)
   - internal domains and personal email addresses
   Use generic placeholders instead: `example.com`, `<project-path>`, `$SKILL_DIR`.
   Derive paths at runtime (e.g. `dirname "$0"`) rather than hard-coding them.

3. **Run the leak-check locally:**
   ```bash
   ./scripts/scrub-check.sh
   ```
   It must exit `0`. CI runs the same check on your PR.

4. **Register it** in three places so both install paths pick it up:
   - add a row to the skill table in `README.md`
   - add it to the `SKILLS` list in `scripts/install.sh`
   - bump `version` in `plugins/fw/.claude-plugin/plugin.json` and
     `.claude-plugin/marketplace.json`

Then open a PR.

## Third-party skills

If the skill (or part of it) comes from someone else, confirm its license permits
redistribution, **vendor the files** (no git submodules / gitlinks in this repo),
and add an attribution block to `NOTICE`. If the license is unclear or restrictive,
don't bundle it — link to the upstream installer from the README instead.

## What belongs here vs. stays private

Publish skills that are genuinely **reusable and self-contained**. Skills that are
welded to private infrastructure (internal APIs, our databases, credential stores)
belong in the private config repo, not here.
