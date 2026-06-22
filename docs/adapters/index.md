# Adapters

This subsystem holds the thin host-adapter shims that sit between an external host
(Claude, Codex, Hermes, OpenClaw) and the tutor engine. Each host speaks its own hook
JSON dialect; the adapters normalize that JSON to and from the canonical lifecycle events
the rest of the system understands, so the engine never has to know which host invoked it.
The shims stay deliberately thin — they translate and declare capabilities, they do not
own decision logic.

## Contract

- `src/language_tutor/adapters/base.py` — the adapter Protocol (`JsonCommandRunner` and
  the base shape) plus the contracts (drawn from `schemas.py`) every host adapter must
  satisfy. This is the seam the engine depends on rather than any concrete host.

## Host shims

- `src/language_tutor/adapters/claude.py`, `src/language_tutor/adapters/codex.py`,
  `src/language_tutor/adapters/hermes.py`, `src/language_tutor/adapters/openclaw.py` —
  one module per supported host, translating that host's hook payloads into canonical
  lifecycle events (and back) at runtime.

## Capability registry

- `src/language_tutor/adapters/registry.py` — the single source of truth for each host's
  capability profile (supported flows, lifecycle start/end values, boot triggers). Host
  shims may translate runtime behavior, but capability declarations stay centralized here
  to keep flow names, lifecycle values, and boot triggers DRY.
