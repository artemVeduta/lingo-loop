# Installer

This subsystem performs source-backed, privacy-preserving host setup. When a user wires
the tutor into a host, the installer detects what is already present, plans the changes,
applies them, and verifies the result — across one or more selected providers. It is
source-backed (it installs from assets bundled in the repo, not by phoning home) and
privacy-preserving (it does not exfiltrate host state), and it runs through fakeable seams
so the whole flow can be exercised hermetically in tests.

## Orchestration

- `src/language_tutor/installer/service.py` — the orchestrator that drives the
  detect → plan → apply → verify sequence across the selected providers and assembles the
  per-provider results.

## Contract and seams

- `src/language_tutor/installer/protocol.py` — the `ProviderInstaller` Protocol plus the
  `InstallerContext` that bundles the filesystem and command-runner seams and the
  bundled-asset root each provider receives.
- `src/language_tutor/installer/seams.py` — the fakeable filesystem and command-runner
  seams (real implementations plus the interfaces tests substitute) that keep installs
  hermetic.
- `src/language_tutor/installer/assets.py` — locates and reads the bundled assets the
  installer writes into a host.

## Provider registry

- `src/language_tutor/installer/registry.py` — declares the supported provider IDs and
  builds the per-host installer for a given provider.
- `src/language_tutor/installer/providers/` — the per-host `ProviderInstaller`
  implementations: `base.py`, `claude.py`, `codex.py`, `hermes.py`, `openclaw.py`.
