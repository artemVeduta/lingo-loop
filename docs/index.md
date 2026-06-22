---
okf_version: "0.1"
---

# lingo-loop knowledge bundle

An Open Knowledge Format (OKF) v0.1 bundle. Lifecycle policy:
[/conventions/documentation.md](/conventions/documentation.md).

## Repo-wide

- [Conventions](/conventions/index.md) - repo-wide prescriptive rules
- [Decisions](/decisions/index.md) - durable architectural decisions
- [Specifications](/specifications/index.md) - how the system works: mechanics, schemas, requirements
- [Glossary](/glossary/index.md) - repo-wide domain terms
- [References](/references/index.md) - external material and project research mirrored as concepts

## Subsystems

- [Adapters](/adapters/index.md) - host-adapter shims that normalize host hook JSON to and from canonical lifecycle events
- [Data access layer](/dal/index.md) - persistence boundary: YAML config plus an append-only SQLite event ledger over XDG paths
- [Installer](/installer/index.md) - source-backed, privacy-preserving host setup that detects, plans, applies, and verifies per provider
- [Engine](/engine/index.md) - pure, golden-tested core decision logic: contracts, lifecycle, SRS, scoring, learning modes, progress
- [CLI](/cli/index.md) - the single `tutor` Click entrypoint that user-facing skills shell out to

## Guides

- [Configuration](/configuration.md) - how the tutor CLI is configured via profile/preferences YAML and env vars
- [Privacy](/privacy.md) - local-first data handling: no telemetry, everything on the user's machine
- [Troubleshooting](/troubleshooting.md) - common install-time, runtime, and host-wiring errors with recovery steps
- [Install](/install/index.md) - per-host install guides (Claude, Codex, Hermes, OpenClaw)

## Superseded

- [Architecture (moved)](/ARCHITECTURE.md) - superseded pointer to [/specifications/architecture-overview.md](/specifications/architecture-overview.md)
