---
name: improve-codebase-architecture
description: Explicit compatibility shortcut for architectureaudit. Use only when the user invokes /improve-codebase-architecture or selects this alias.
disable-model-invocation: true
uses:
  - skill: architectureaudit
    relation: delegates
---

Follow `wtf:architectureaudit` with the user's arguments unchanged (`wtf-architectureaudit` on a
clone install). If a Skill tool is unavailable, read the sibling
`../architectureaudit/SKILL.md` (`../wtf-architectureaudit/SKILL.md` on a clone install).
The workflow lives only in architectureaudit.
