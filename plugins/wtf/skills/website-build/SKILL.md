---
name: website-build
description: Explicit compatibility shortcut for websitegrounding. Use only when the user invokes /website-build or selects this alias.
disable-model-invocation: true
uses:
  - skill: websitegrounding
    relation: delegates
---

Follow `wtf:websitegrounding` with the user's arguments unchanged (`wtf-websitegrounding` on a
clone install). If a Skill tool is unavailable, read the sibling
`../websitegrounding/SKILL.md` (`../wtf-websitegrounding/SKILL.md` on a clone install).
The workflow lives only in websitegrounding.
