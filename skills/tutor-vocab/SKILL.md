---
name: tutor-vocab
description: Practice due vocabulary through the local tutor CLI.
---

Use this when learner wants vocabulary review, starter vocabulary, or answer correction.

Run only `bin/tutor` for stateful work:

- Start queue: `bin/tutor vocab start --json`
- Record answer once: `bin/tutor vocab answer --json '<payload>'`

Do not implement SM-2 or persistence in this skill.
