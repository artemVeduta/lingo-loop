---
name: tutor-writing
description: Free writing prompt and structured feedback orchestration.
---

Use this when learner wants free writing or structured correction.

Flow:

1. Get prompt with `bin/tutor writing prompt --json`.
2. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object.
3. Persist validated feedback with `bin/tutor writing record --json '<payload>'`.
4. Render with `bin/tutor render feedback --json '<feedback>'`.

Do not persist directly or render through another LLM step.
