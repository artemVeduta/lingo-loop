---
name: tutor-reading
description: Use when the learner wants to read a passage and answer comprehension questions, or reconstruct a text transcript drill (text-only, no audio). Not for free writing, vocabulary review, or guided lessons.
---

Use this when the learner wants reading comprehension practice or a text-only transcript
drill. Transcript drills are a text-only submode of this skill (`mode:"transcript"`); they
are not audio and there is no separate transcript skill.

Run only `bin/tutor` for stateful work:

1. Generate a candidate exercise (JSON) for the learner's target language and level.
2. Validate it: `bin/tutor reading start --json '{"mode":"comprehension","candidate":{...}}'`
   (use `"mode":"transcript"` for transcript drills).
3. If validation fails, regenerate the candidate once, then validate again. After one
   failed repair, stop and tell the learner the exercise could not be prepared.
4. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object about the learner's answer.
5. Persist: `bin/tutor reading record --json '<TextModalityRecordInput>'`.
6. Render feedback with `bin/tutor render feedback --json '<feedback>'`.

The CLI owns validation, output budgets, scoring metadata, persistence, and progress.
Do not invent corrections, persist directly, render through another LLM step, or imply
audio playback. Keep everything text-only.
