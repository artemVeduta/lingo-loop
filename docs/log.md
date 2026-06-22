# Bundle change log

## 2026-06-22

- **Initialization**: Established the OKF v0.1 bundle skeleton (root, conventions,
  glossary, references) and installed the validator, the `docs-authoring` rule, and the
  `docs-add` / `docs-validate` skills.
- **Creation**: Authored the governance concept
  [Documentation lifecycle policy](/conventions/documentation.md) and the
  [OKF reference](/references/okf.md).
- **Migration**: Restructured architecture + requirements docs into
  [/specifications/](/specifications/index.md) (Specification); superseded-pointer stubs
  left at `/ARCHITECTURE.md`, `/internal/ARCHITECTURE.md`, `/internal/REQUIREMENTS.md`.
- **Migration**: Moved the stack doc to
  [/decisions/technology-stack.md](/decisions/technology-stack.md) (Decision) with a
  superseded stub in `internal/`; made `internal/constitution.md` OKF-conformant in place
  (Convention).
- **Migration**: Moved internal research into [/references/](/references/index.md) —
  [pitfalls](/references/pitfalls.md),
  [project overview](/references/project-overview.md) (dropped the gsd-transition evolution
  section), [maintainer guide](/references/maintainer-guide.md); superseded stubs left in
  `internal/`.
- **Migration**: Brought the public guides (configuration, privacy, troubleshooting,
  `install/*`) to OKF conformance as Reference; added the `install/` index.
- **Creation**: Seeded subsystem orientation nodes — [adapters](/adapters/index.md),
  [dal](/dal/index.md), [installer](/installer/index.md), [engine](/engine/index.md),
  [cli](/cli/index.md).
- **Deprecation**: Removed stale planning meta — `internal/ROADMAP.md`,
  `internal/SUMMARY.md`, `internal/FEATURES.md` (tasks tracked in Linear).
