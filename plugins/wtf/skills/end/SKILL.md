---
name: end
description: |
  Explicit shortcut for wrapup. Use only when the user invokes /end or selects this alias.
disable-model-invocation: true
department: ops
uses:
  - skill: wrapup
    relation: delegates
---

Follow the `wrapup` skill with the user's arguments unchanged (`manual`, `skip-map`,
`skip-cleanup`, `keep-servers`, `force`). If the harness has a Skill tool, invoke
`wtf:wrapup` (`wtf-wrapup` on a clone install). Otherwise read the sibling
`../wrapup/SKILL.md` (`../wtf-wrapup/SKILL.md` on a clone install) and follow it.
The session-closing workflow lives only there.
