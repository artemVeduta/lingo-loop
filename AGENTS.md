<!-- SPECKIT START -->
For additional context about technologies, project structure, shell commands,
and design decisions, read `docs/internal/ROADMAP.md` for current phase scope and
`specs/006-agent-adapter-setup/plan.md` for the current implementation
plan. Use `specs/005-text-modalities/plan.md` as the prior text-flow baseline,
`specs/004-richer-feedback-progress/plan.md` as the prior feedback/progress
baseline, and `specs/003-smarter-engine/plan.md` as the prior engine baseline.
Enforce `.specify/memory/constitution.md` for architecture, scope, data
ownership, testing, and review gates.
<!-- SPECKIT END -->

**Documentation**
[ARCHITECTURE.md](docs/ARCHITECTURE.md)
[FEATURES.md](docs/internal/FEATURES.md)
[PITFALLS.md](docs/internal/PITFALLS.md)
[PROJECT.md](docs/internal/PROJECT.md)
[REQUIREMENTS.md](docs/internal/REQUIREMENTS.md)
[ROADMAP.md](docs/internal/ROADMAP.md)
[STACK.md](docs/internal/STACK.md)
[SUMMARY.md](docs/internal/SUMMARY.md)

**Skills**:
Never auto-invoke Superpowers skills. Invoke only when explicitly requested.
Skill creation/update work must use a subagent and the local writing-skills
helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`.
