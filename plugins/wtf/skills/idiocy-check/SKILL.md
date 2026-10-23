---
name: idiocy-check
description: Explicit compatibility shortcut for idiocycheck. Use only when the user invokes /idiocy-check or selects this alias.
disable-model-invocation: true
uses:
  - skill: idiocycheck
    relation: delegates
---

Follow `wtf:idiocycheck` with the user's arguments unchanged (`wtf-idiocycheck` on a
clone install). If a Skill tool is unavailable, read the sibling
`../idiocycheck/SKILL.md` (`../wtf-idiocycheck/SKILL.md` on a clone install).
The workflow lives only in idiocycheck.
