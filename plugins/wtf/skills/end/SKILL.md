---
name: end
description: |
  Alias for wrapup. Use when the user says "end", "/end", "end the skill" or
  "end it here" meaning: close out the coding session. Runs the wrapup skill
  with the same arguments.
department: ops
---

This is an alias. Invoke the `wrapup` skill (`wtf:wrapup`, or `wtf-wrapup` on a
clone install) through the Skill tool, passing along any arguments given here
unchanged (`manual`, `skip-map`, `skip-cleanup`, `keep-servers`, `force`). Then
follow that skill. Do not run any steps from this file.
