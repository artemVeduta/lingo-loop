---
name: tutor-lesson
description: Use when the learner wants a guided micro-lesson on one weak tag or one chosen topic (one explanation plus one practice step). Not for reading comprehension, free writing, vocabulary review, or progress reports.
---

Use this when the learner wants a short guided lesson on one weak area or a topic they
pick. A micro-lesson covers exactly one bounded topic plus a single practice step.

Run only `bin/tutor` for stateful work:

1. Pick one focus: a learner-chosen topic, or a weak tag from `bin/tutor progress --json`.
2. Generate a candidate lesson (JSON) for the learner's target language and level with one
   explanation and one practice step.
3. Validate it: `bin/tutor lesson start --json '{"candidate":{...}}'`.
4. If validation fails, regenerate the candidate once, then validate again. After one
   failed repair, stop and tell the learner the lesson could not be prepared.
5. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object about the practice answer.
6. Persist: `bin/tutor lesson record --json '<TextModalityRecordInput>'`.
7. Render feedback with `bin/tutor render feedback --json '<feedback>'`.

The CLI owns validation, output budgets, scoring metadata, persistence, and progress.
Do not invent corrections, persist directly, render through another LLM step, or expand
the lesson beyond one bounded topic.
