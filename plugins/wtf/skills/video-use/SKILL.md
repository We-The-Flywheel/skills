---
name: video-use
description: Explicit compatibility shortcut for videoedit. Use only when the user invokes /video-use or selects this alias.
disable-model-invocation: true
uses:
  - skill: videoedit
    relation: delegates
---

Follow `wtf:videoedit` with the user's arguments unchanged (`wtf-videoedit` on a
clone install). If a Skill tool is unavailable, read the sibling
`../videoedit/SKILL.md` (`../wtf-videoedit/SKILL.md` on a clone install).
The workflow lives only in videoedit.
