# Flywheel Skills public distribution

Public installable marketplace for reusable agent skills. This repository is a
reviewed file-snapshot distribution mirror; maintainer development happens in
the private canonical workspace described in README.

## Sources and scope
- [README.md](README.md): installation, skill catalog and supported distribution paths.
- [CONTRIBUTING.md](CONTRIBUTING.md): public-content restrictions, metadata and contribution process.
- [plugins/wtf/skills/](plugins/wtf/skills/): actual shared skill implementations.
- [scripts/install.sh](scripts/install.sh): legacy clone installer; preserve existing installations and alias backups.

## Hard boundaries
- Nothing confidential may land here: no private history, personal skills, internal hosts/domains/paths, credentials or personal addresses.
- Use generic placeholders and runtime-relative paths; follow CONTRIBUTING's exact allowed environment reference rules.
- Preserve public install URLs and skill names. Accept public contributions through review and reconcile them into the canonical source before a new export.
- Skill frontmatter names match their folder and remain unprefixed; the plugin supplies `wtf:`.
- Update README registration, installer list and both marketplace/plugin versions together for a new skill.
- Declare `uses:` only for actual dependencies, with the schema in CONTRIBUTING.
- Keep aliases explicit and canonical automatic triggers unique. Archive retired skills outside plugin discovery.

## Verification
- Run `bash scripts/scrub-check.sh`; it must exit zero before publication.
- Validate changed shell entrypoints with `bash -n <script>` and run the affected skill's own checks where documented.
- There is no root application build/test runner. Verify install/catalog/version consistency for package changes.
- Do not copy private development instruction paths or internal deployment details into this public instruction file.
