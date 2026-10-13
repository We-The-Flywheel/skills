# Step 3c-3e: other servers, temp files, /tmp scratch

Moved verbatim from `SKILL.md`; read at the step that points here.

**3c. Detect other listening dev servers (confirm before killing).** Skip if `keep-servers`.

```bash
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null \
  | grep -iE 'node|bun|vite|next|hugo|astro|deno|python|php|ruby|rails|webpack' \
  | awk '{print $1, $2, $9}' | sort -u
```

If any are found that this session did NOT start: list them (process, PID, port) and ask "Shut down these dev servers too?" (y/N). Default **NO** — never auto-kill a server this session didn't start.

**Safety:** never kill non-dev-server processes (databases, system services, editors/IDEs, the Claude Code process itself). Local-only — never `ssh` to a server and stop remote/production services here. If detection is ambiguous, list and ask.

**3d. Other temp files (confirm before deleting):**

```bash
find . -type f \( -name "*.tmp" -o -name "*.swp" -o -name "*~" -o -name "*.orig" \) \
  -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null
find . -type d \( -name ".pytest_cache" -o -name ".ruff_cache" \) \
  -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.venv/*" 2>/dev/null
```

Python cache (`*.pyc`, `__pycache__`, `.mypy_cache`) is excluded — it regenerates. If found: list clearly, ask "Remove these temporary files?" (y/N), default NO.

**3e. Session `/tmp` scratch artifacts:** if this session wrote scratch files to the system temp dir (screenshots, capture prefixes, image-staging dirs), list and remove them with the same y/N confirmation. Only target paths this session actually wrote — never blanket-delete `/tmp`.
