# Phase 8 — Automated QA Agent Harness + Adapter Expansion

**Date:** 2026-05-23
**Status:** Design (pre-plan)
**Branch (target):** `008-qa-harness-agent`
**Predecessor:** Phase 7 (hook-free incremental lifecycle, branch `007-hookfree-incremental-lifecycle`)
**Successor:** Phase 9 (audio modalities)

## Goal

Replace manual dogfood testing inside Claude Code with a reproducible, headless QA loop. A second agent plays a learner persona, drives a real tutor session end-to-end, and a separate judge agent grades the run against a structured rubric while also recording in-character "feelings about the lesson." Output is per-run artifacts (transcript, state diff, critique JSON + free-form notes) suitable for trend tracking and bug triage.

Secondary goal: extend the Phase 6 adapter framework to cover Antigravity and OpenCode so the harness can drive learners and judges across all supported hosts.

## Non-Goals

- Replacing existing unit / contract / migration / packaging tests.
- Live CI runs against real LLMs (gated behind opt-in marker; costs tokens).
- Auto-promoting critique verdicts into release gates. Critique is advisory.
- Building a UI. Reports are markdown + JSON on disk.
- Audio scenarios. Audio rides Phase 9 and reuses this harness.

## Background

Tutor is exercised today by the maintainer manually running tutor skills inside Claude Code, reading the conversation, and forming a subjective judgment. This is slow, non-reproducible, and the qualitative signal disappears the moment the session closes. The Phase 6 capability layer + Phase 7 hook-free lifecycle now make headless tutor sessions deterministic enough that an LLM-driven learner can be substituted for the human, and a second pass can convert the conversation into a structured critique.

## Architecture

Three roles, two processes per run, one transcript artifact:

```
┌──────────────┐     spawns      ┌──────────────────────────┐
│ qa harness   │ ───────────────▶│ <driver> -p  (LEARNER)   │
│ (python CLI) │                 │  • tutor plugin loaded   │
│              │                 │  • persona prompt         │
│              │                 │  • fixture profile env   │
│              │ stream-json     │  • invokes tutor skills  │
│              │◀────────────────│    → tutor CLI → SQLite  │
│              │                 └──────────────────────────┘
│              │
│              │     spawns      ┌──────────────────────────┐
│              │ ───────────────▶│ <driver> -p  (JUDGE)     │
│              │                 │  • reads transcript +    │
│              │                 │    rubric template        │
│              │ critique json   │  • emits Critique JSON +  │
│              │◀────────────────│    free-form notes        │
└──────────────┘                 └──────────────────────────┘
       │
       ▼
  reports/<ts>-<scenario>/
    transcript.jsonl
    tutor-state-diff.json
    critique.json
    critique.md
    tutor-errors.log    (if any)
```

The harness is a thin Python orchestrator in `tests/qa/`. It is not shipped to end users and does not introduce new production CLI surface. Invocation:

```
python -m tests.qa run <scenario>            # default learner+judge from yaml
python -m tests.qa run <scenario> \
    --learner-driver codex --judge-driver claude     # override drivers
python -m tests.qa list-scenarios
python -m tests.qa snapshot new|promote|list # fixture snapshot mgmt
```

## Components

```
tests/qa/
├── __init__.py
├── harness.py          # orchestrator: argparse, scenario loop, report writer
├── learner.py          # spawn+drive learner driver; capture stream-json
├── judge.py            # spawn judge driver; rubric pass; pydantic parse
├── fixtures.py         # fixture path resolver + reset_fixture_profile()
├── drivers/
│   ├── base.py         # LearnerDriver / JudgeDriver protocols
│   ├── _matrix.py      # capability matrix (which driver has tutor plugin)
│   ├── claude.py
│   ├── codex.py
│   ├── hermes.py
│   ├── openclaw.py
│   ├── agy.py          # antigravity (lifted exclusion — see Adapter Expansion)
│   ├── opencode.py
│   └── mock.py         # deterministic canned-response driver for CI smoke
├── scenarios/
│   ├── reading-a2.yaml
│   ├── vocab-drill.yaml
│   └── full-session.yaml
├── personas/
│   ├── beginner-uk.md
│   └── intermediate-uk.md
├── rubric.md
└── reports/            # gitignored; one dir per run
```

Each module has one job:
- **harness** — CLI parsing, scenario selection, calls learner then judge, writes report. No tutor or LLM knowledge.
- **learner** — only knows how to spawn a learner driver, feed the opening turn, and read stream-json until a terminal condition. Returns a `Transcript` object.
- **judge** — takes `Transcript` + `StateDiff` + rubric, returns `Critique` pydantic. Schema-validated, one retry on parse failure.
- **fixtures** — fixture dir resolution, `reset_fixture_profile(seed_id)`, snapshot lifecycle.
- **drivers/** — pure adapter layer per host CLI; the rest of the harness is host-agnostic.

## Data flow

1. harness loads scenario yaml → `Scenario` pydantic (persona path, target skill, max_turns, seed_snapshot_id, success_signals, learner_driver, judge_driver, budgets).
2. `fixtures.reset_fixture_profile(seed_snapshot_id)`:
   - acquire `flock` on `qa-learner/.lock`
   - `rmtree` working fixture
   - `copytree` from `data/fixtures/qa-snapshots/<seed_id>`
   - assert snapshot migration head equals current `migrations/` head; fail loud otherwise.
3. `learner.run(scenario, persona)`:
   - resolve driver from `drivers/_matrix.py`; verify `shutil.which(driver.bin)`; fail with `EX_UNAVAILABLE` if missing.
   - spawn driver with env injection:
     ```
     TUTOR_DATA_DIR=data/fixtures/qa-learner
     XDG_DATA_HOME=data/fixtures/qa-learner/xdg
     XDG_CONFIG_HOME=data/fixtures/qa-learner/xdg-config
     ```
   - assert none of these env values resolve under `$HOME`.
   - inject system prompt = `persona.md` + scenario goal + "do not break character; do not ask meta questions about tutor."
   - inject first user turn = `scenario.opening_message`.
   - read stream-json events from driver stdout; the driver's own loop generates the next learner reply (multi-turn `--resume` or equivalent). Harness does not generate learner replies in Python.
   - stop on: `max_turns` reached, `scenario.success_signal` matched, tutor returns terminal state, persona-break heuristic (no tutor tool call in N consecutive turns), or token budget exceeded.
   - dump `transcript.jsonl` and the post-run SQLite snapshot.
4. `state_diff = sqlite_diff(seed_snapshot, fixture_after)` → `StateDiff` JSON.
5. `judge.run(transcript, state_diff, rubric)`:
   - spawn judge driver (separate process; persona contamination avoided).
   - system prompt = `rubric.md`; user message = transcript + state_diff + scenario manifest.
   - require `--output-format json`; pydantic parse `Critique`.
   - one retry on parse failure with the prior raw output appended. Second failure writes `critique.raw.txt` and harness exits non-zero.
6. harness writes `reports/<ts>-<scenario>/` and emits a short verdict line on stdout.

The driver loop (step 3) is the only place that knows about a specific host CLI. The judge (step 5) is host-agnostic — any LLM CLI that accepts a prompt and returns JSON works.

## Scenario format

`tests/qa/scenarios/reading-a2.yaml`:

```yaml
name: reading-a2
persona: beginner-uk           # → personas/beginner-uk.md
target_skill: tutor-reading
learner_driver: claude         # default; overridable from CLI
judge_driver: claude
seed_snapshot: a2-baseline
opening_message: "Я хочу почитати щось коротке."
max_turns: 12
success_signals:
  - tutor_event: reading.completed
  - tutor_event: progress.recorded
budgets:
  learner_tokens: 30000
  judge_tokens: 8000
```

## Persona format

`tests/qa/personas/beginner-uk.md` — plain markdown. Includes: role, CEFR level, native language, learning goal, expected behaviors (ask for translation when stuck, make typical en→uk interference errors), forbidden behaviors (do not break character, do not ask meta questions about tutor, do not refuse).

## Rubric and Critique shape

`tests/qa/rubric.md` is the judge's system prompt and defines the schema:

```json
{
  "scenario": "reading-a2",
  "scores": {
    "pedagogy":              {"score": 1, "quote": "...", "why": "..."},
    "tone":                  {"score": 1, "quote": "...", "why": "..."},
    "difficulty_fit":        {"score": 1, "quote": "...", "why": "..."},
    "error_tagging":         {"score": 1, "quote": "...", "why": "..."},
    "engagement":            {"score": 1, "quote": "...", "why": "..."},
    "instruction_adherence": {"score": 1, "quote": "...", "why": "..."}
  },
  "bugs": [{"severity": "high|med|low", "evidence": "...", "where": "turn 4"}],
  "vibes": "free-form in-character learner reflection paragraph",
  "verdict": "ship | iterate | broken"
}
```

Each score is integer 1–5 and must cite a transcript span (`quote`) to prevent hallucinated grading. `vibes` is the only free-form section — captures the qualitative "feelings about the lesson" goal.

## Driver layer

`tests/qa/drivers/base.py`:

```python
class LearnerDriver(Protocol):
    name: str
    bin: str
    has_tutor_plugin: bool

    def spawn(self, cwd: Path, env: dict[str, str], system_prompt: str) -> Process: ...
    def send_turn(self, proc: Process, text: str) -> None: ...
    def read_events(self, proc: Process) -> Iterator[StreamEvent]: ...
    def terminate(self, proc: Process) -> None: ...

class JudgeDriver(Protocol):
    name: str
    bin: str

    def grade(self, system: str, user: str, *, token_budget: int) -> str: ...  # raw JSON string
```

Driver matrix (`_matrix.py`) declares for each driver: whether it has a tutor plugin shipped, its headless invocation form, its stream-json schema flavor. Drivers without `has_tutor_plugin = True` may only be used as judges; using one as a learner raises at scenario load.

### Adapter expansion (lifts Phase 6 exclusion)

Phase 6 explicitly excluded Antigravity and never included OpenCode. Phase 8 lifts both:

- Remove `HostId` reject for `antigravity` and add `opencode` to the enum.
- Delete `tests/packaging/test_host_setup_profiles.py::test_no_antigravity_artifacts`; replace with positive coverage.
- Add `agy` and `opencode` to `AdapterCapabilityProfile`, `adapters/registry.py`, manual-install reports, and capability-profile contracts under `specs/006-agent-adapter-setup/`. Spec 006 gets an amendment note pointing at Phase 8.
- Ship `tutor` plugin artifacts for both hosts under `agy-plugin/` and `opencode-plugin/` (mirroring `.codex-plugin/`).
- `has_tutor_plugin = True` for all four learner drivers.

This is bundled into Phase 8 and parallelizable across subagents.

## Fixture isolation and snapshots

- Fixture working dir: `data/fixtures/qa-learner/` (gitignored).
- Golden snapshots: `data/fixtures/qa-snapshots/<id>/` (committed). Each snapshot contains `profile.yaml`, `preferences.yaml`, `state.sqlite`, and any cached artifacts.
- `fixtures.reset_fixture_profile(seed_id)` is the only path that touches the fixture working dir.
- Concurrent runs are mutually exclusive on `qa-learner/.lock` via `flock`. Second run blocks or, with `--no-wait`, exits.
- Snapshot management CLI:
  - `python -m tests.qa snapshot new <id>` — capture current `qa-learner/` as new seed.
  - `python -m tests.qa snapshot promote <run-id> <new-seed-id>` — copy a finished run's end-state to a new seed (enables multi-day continuity scenarios).
  - `python -m tests.qa snapshot list`.
- Snapshot schema-drift guard: on reset, the snapshot's recorded migration head must equal current `migrations/` head; mismatch fails loud with the bump procedure linked in `tests/qa/README.md`.

## Error handling and edge cases

| Case | Behavior |
|---|---|
| Driver CLI binary missing | Fail at scenario load with `EX_UNAVAILABLE` and install hint from matrix. No silent skip. |
| Learner persona break (goes meta or stalls) | Detect via `max_turns` and "no tutor tool call in N consecutive turns." End run, mark `verdict=broken`; judge still runs and flags persona break as a `bug`. |
| Tutor CLI crash | Non-zero exit captured in stream-json tool result; stderr → `reports/<run>/tutor-errors.log`. No retry. Surfaces as bug in critique. |
| Judge invalid JSON | One retry with prior raw output appended. Second failure → write `critique.raw.txt`, harness exits non-zero. |
| Token budget exceeded | Kill driver; mark `verdict=broken` with `reason=budget_exceeded`. |
| Snapshot schema drift | Fail at reset, not mid-run. Documented bump procedure. |
| Concurrent runs | `flock` on `qa-learner/.lock`; second run waits or `--no-wait` exits. |
| Judge LLM/API outage | Distinguish from invalid-JSON via exit code. Write partial report (transcript + state-diff present, no critique). |

## Testing the harness itself

- **Unit** (`tests/unit/qa/`):
  - `test_scenario_load.py` — yaml → `Scenario` pydantic; missing fields fail loud.
  - `test_fixture_reset.py` — temp dir, fake snapshot, assert tree copied + lock honored.
  - `test_driver_matrix.py` — capability lookups, missing-binary detection (monkeypatch `shutil.which`).
  - `test_critique_schema.py` — `Critique` pydantic round-trip; invalid JSON rejected.
  - `test_env_isolation.py` — assert no injected env var resolves under `$HOME`.
- **Contract** (`tests/qa/contract/`):
  - Each driver implements `LearnerDriver` / `JudgeDriver` protocol; one test per driver verifies surface.
  - Recorded fixture transcripts (no live LLM) feed judge → schema-valid critique.
- **Smoke** (`tests/qa/smoke/`):
  - One end-to-end run using `MockDriver` (deterministic canned responses). Exercises the full pipeline without burning real tokens. Runs in CI.
- **Live** (opt-in, not in CI):
  - `pytest -m qa_live` runs one real scenario per learner driver. Manual trigger.

Pyramid: many cheap unit tests, one mock-driven smoke run in CI, live runs behind a marker.

## Out-of-scope (deferred)

- Audio scenarios (Phase 9).
- Multi-turn judge dialog (judge stays single-shot; observer agent considered then rejected on KISS grounds).
- Auto-promoting verdicts into release gates.
- Cross-run trend dashboards beyond raw JSON on disk.
- Distributed / parallel scenario execution.

## Open questions

None blocking. Drivers' exact stream-json schema differences will be discovered during driver-layer implementation and resolved per-driver in `drivers/<host>.py`.

## Dependencies / sequencing

- Hard prereq: Phase 7 (hook-free incremental lifecycle) merged, so headless lifecycle is deterministic.
- Adapter expansion (`agy`, `opencode`) and harness/drivers/scenarios land in the same phase. Subagents parallelize:
  - **Subagent A** — adapter expansion (spec 006 amendment, `HostId`, registry, packaging tests, plugin artifacts).
  - **Subagent B** — harness core (`harness.py`, `learner.py`, `judge.py`, `fixtures.py`, scenario/persona/rubric data).
  - **Subagent C** — driver layer (`drivers/*`, capability matrix, `MockDriver`, contract tests).
- Phase 9 (audio) consumes this harness for pronunciation / listening scenarios.
