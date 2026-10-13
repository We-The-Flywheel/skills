# Step 7a: gather context

Moved verbatim from `SKILL.md`; read at the step that points here.

```bash
ls -la
find . -maxdepth 2 -type d 2>/dev/null | head -30
git log --oneline -20 2>/dev/null
git diff --name-status HEAD~5..HEAD 2>/dev/null
# Tech stack detection (whichever exist)
head -50 package.json pyproject.toml requirements.txt 2>/dev/null
head -30 Cargo.toml go.mod composer.json 2>/dev/null
# Existing documentation
head -100 AGENTS.md CLAUDE.md README.md 2>/dev/null
cat PROJECT_MAP.md 2>/dev/null
```
