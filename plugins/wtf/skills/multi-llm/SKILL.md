---
name: multi-llm
description: Explicit compatibility shortcut for multillm. Use only when the user invokes /multi-llm or selects this alias.
disable-model-invocation: true
department: engineering
uses:
  - skill: multillm
    relation: delegates
---

Follow the `multillm` skill with the user's arguments unchanged. If the harness
has a Skill tool, invoke `wtf:multillm` (`wtf-multillm` on a clone install).
Otherwise read the sibling `../multillm/SKILL.md`
(`../wtf-multillm/SKILL.md` on a clone install) and follow it.
The workflow and council scripts live only in multillm.
