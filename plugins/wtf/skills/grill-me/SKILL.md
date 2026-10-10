---
name: grill-me
description: Explicit shortcut for grilling. Use only when the user invokes /grill-me or selects this alias.
disable-model-invocation: true
department: engineering
uses:
  - skill: grilling
    relation: delegates
---

Follow the `grilling` skill with the user's arguments unchanged. If the harness has a
Skill tool, invoke `wtf:grilling` (`wtf-grilling` on a clone install). Otherwise read
the sibling `../grilling/SKILL.md` (`../wtf-grilling/SKILL.md` on a clone install)
and follow it. The interview and open-questions workflow live only there.
