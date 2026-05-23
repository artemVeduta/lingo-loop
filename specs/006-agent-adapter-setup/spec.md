# Feature Specification: Agent Adapter Setup

**Feature Branch**: `006-agent-adapter-setup`

**Created**: 2026-05-22

**Status**: Draft

**Input**: User description: "006. Hermess - https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions, openclaw - https://docs.openclaw.ai/plugins/building-plugins#building-plugins, claude - https://code.claude.com/docs/en/plugins, codex - https://developers.openai.com/codex/plugins/build, antigravity - skip. You required to go to this urls to researchabout how to setup eeach agent. Implementation must be - for each agent spawn sub-agent to implementation"

## Clarifications

### Session 2026-05-22

- Q: Which flows must every host pass for representative tutor-flow verification? → A: All Phase 5 text flows: reading, lesson, transcript, vocab, writing, progress.
- Q: What counts as clean-enough setup verification for this feature? → A: Manual provider install test.
- Q: How should readiness handle a host that cannot pass one representative flow? → A: Block; documented skips allowed.
- Q: Where should source-backed host setup profiles be recorded as the source of truth? → A: Versioned contract files under `specs/006-agent-adapter-setup/contracts/host-setup-profiles/`.
- Q: Who should create each `contracts/host-setup-profiles/` file? → A: Host subagent owns it after main maintainer provides full context.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Source-Backed Host Setup Scope (Priority: P1)

A maintainer defines the supported host setup targets from the official Hermes, OpenClaw, Claude, and Codex documentation so every adapter rollout has a clear distribution and verification path before implementation begins.

**Why this priority**: Host-specific setup is the main risk for this phase. Each supported host must follow its own official setup model instead of copying the Claude-only path.

**Independent Test**: Can be tested by reviewing the versioned host setup profile contracts and confirming each included host has an official source URL, supported setup path, install/update expectations, user-owned data boundaries, and verification expectations.

**Acceptance Scenarios**:

1. **Given** the feature scope is reviewed, **When** supported hosts are listed, **Then** Hermes, OpenClaw, Claude, and Codex are included with their official setup source references.
2. **Given** the feature scope is reviewed, **When** excluded hosts are listed, **Then** Antigravity is explicitly skipped with no implementation tasks or deliverables.
3. **Given** a host setup requirement is proposed, **When** the official source does not support that setup behavior, **Then** the requirement is rejected or documented as out of scope.
4. **Given** an official source changes before implementation, **When** planning starts, **Then** the affected host setup expectations are re-checked against the current source.
5. **Given** host setup planning is reviewed, **When** profile evidence is inspected, **Then** source-backed host setup profiles are stored as versioned contract files under `specs/006-agent-adapter-setup/contracts/host-setup-profiles/`.

---

### User Story 2 - Independent Per-Host Implementation Slices (Priority: P1)

A maintainer implements each supported host through a separate assigned subagent so Hermes, OpenClaw, Claude, and Codex setup work can be developed, verified, and reviewed independently.

**Why this priority**: The user explicitly requires one subagent per agent implementation. Independent slices also reduce cross-host coupling and make setup regressions easier to isolate.

**Independent Test**: Can be tested by checking implementation evidence and confirming each host has exactly one primary subagent owner, a host-specific work summary, changed-file report, setup decisions, and verification result.

**Acceptance Scenarios**:

1. **Given** implementation begins for Hermes, **When** work is assigned, **Then** the main maintainer provides the full context package and a Hermes-specific subagent owns the Hermes setup slice, including its host setup profile contract, and reports source usage plus verification evidence.
2. **Given** implementation begins for OpenClaw, **When** work is assigned, **Then** the main maintainer provides the full context package and an OpenClaw-specific subagent owns the OpenClaw setup slice, including its host setup profile contract, and reports source usage plus verification evidence.
3. **Given** implementation begins for Claude, **When** work is assigned, **Then** the main maintainer provides the full context package and a Claude-specific subagent owns the Claude setup slice, including its host setup profile contract, and reports source usage plus verification evidence without breaking the existing Claude baseline.
4. **Given** implementation begins for Codex, **When** work is assigned, **Then** the main maintainer provides the full context package and a Codex-specific subagent owns the Codex setup slice, including its host setup profile contract, and reports source usage plus verification evidence.
5. **Given** all subagent reports are complete, **When** the main maintainer integrates the work, **Then** every reported changed file is reviewed and cross-host contract compatibility is checked.

---

### User Story 3 - Manual Provider Install And Update Verification (Priority: P2)

A maintainer manually installs the tutor app into each supported provider, then verifies that each supported host can be launched, updated, and inspected using that host's documented setup model.

**Why this priority**: Adapter setup is not complete until a user can reproduce it outside the development machine.

**Independent Test**: Can be tested by manually installing the app into Hermes, OpenClaw, Claude, and Codex through each host's documented install path, launching the tutor surface, checking capability reporting, exercising every Phase 5 text flow (reading comprehension, guided lesson, transcript drill, vocab drill, free-writing feedback, and progress check), and validating that user-owned data is not overwritten during update.

**Acceptance Scenarios**:

1. **Given** the maintainer manually installs the tutor into Hermes, **When** the tutor agent distribution is installed, **Then** the profile can be inspected, launched, updated, and removed while user credentials, memories, sessions, and local state remain user-owned.
2. **Given** the maintainer manually installs the tutor into OpenClaw, **When** the tutor plugin is installed, **Then** the host recognizes the plugin metadata, exposes the intended tools or hooks, and keeps optional side-effectful capabilities opt-in.
3. **Given** the maintainer manually installs the tutor into Claude Code, **When** the tutor plugin is loaded, **Then** the plugin manifest and namespaced skills are recognized and the existing Claude tutor flow still works.
4. **Given** the maintainer manually installs the tutor into Codex, **When** the tutor plugin is added through a marketplace or equivalent local distribution surface, **Then** Codex recognizes the plugin, exposes the tutor skill surface, and supports local iteration before broader sharing.
5. **Given** any included host setup has completed, **When** representative tutor-flow verification runs, **Then** reading comprehension, guided lesson, transcript drill, vocab drill, free-writing feedback, and progress check all complete through that host unless a documented capability limitation gates a specific flow.

---

### User Story 4 - Host-Portable Tutor Behavior (Priority: P2)

A learner receives the same language tutoring behavior on every supported text-capable host, while host-specific setup details remain isolated from pedagogy, scheduling, feedback, and local learner data.

**Why this priority**: The roadmap requires host portability without leaking host mechanics into the tutor core.

**Independent Test**: Can be tested by running the same representative tutor flows through each supported host setup and confirming learning contracts, feedback shape, progress signals, and local data ownership remain consistent.

**Acceptance Scenarios**:

1. **Given** a supported host is installed, **When** a learner starts the tutor, **Then** the host declares its text capability and lifecycle behavior before tutor flows depend on it.
2. **Given** a host lacks Claude-style lifecycle hooks, **When** the tutor starts, **Then** boot context is still built through the documented alternate trigger.
3. **Given** a learner completes every supported representative tutor flow on any supported host, **When** feedback and progress are inspected, **Then** the same validated tutor contracts are used across hosts, and any skipped flow is documented as capability-gated.
4. **Given** a host-specific setup fails, **When** the failure is reported, **Then** the learner receives a clear host-specific setup error without corrupting local tutor state.

### Edge Cases

- Official setup documentation is unreachable or has changed before planning or implementation.
- "Hermess" in the request refers to Hermes Agent from Nous Research.
- A host supports plugins but not lifecycle hooks equivalent to Claude SessionStart or SessionEnd.
- A host supports tools but requires optional enablement for side-effectful or binary-dependent capabilities.
- A host cannot support one representative Phase 5 flow and must gate it through a documented capability limitation.
- A host setup format separates package-owned files from user-owned credentials, memory, sessions, or local state.
- A manual provider install has required host software missing or below the documented minimum version.
- A host requires user-provided API keys or secrets that must not be packaged.
- A host package installs successfully but does not expose the expected tutor entry point.
- A subagent reports changed files outside its assigned host setup scope.
- Two host subagents need to change the same shared contract or conformance fixture.
- The existing Claude adapter works before the feature but fails after host setup changes.
- Antigravity work is accidentally added to tasks, contracts, docs, or tests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST treat the official Hermes, OpenClaw, Claude, and Codex setup documentation named in the feature request as source-of-truth inputs for this feature.
- **FR-002**: System MUST include setup support for Hermes, OpenClaw, Claude, and Codex only; Antigravity MUST remain out of scope for specification, planning, tasks, implementation, and verification.
- **FR-003**: System MUST record a host setup profile for each included host as a versioned contract file under `specs/006-agent-adapter-setup/contracts/host-setup-profiles/`, containing the official source URL, setup package model, required user-provided secrets or environment values, update behavior, user-owned data boundaries, and verification expectations.
- **FR-004**: Hermes setup MUST support a profile-distribution model: a shareable agent profile with a manifest, prompt/personality content, bundled skills or scheduled tasks where applicable, MCP configuration where applicable, required environment declarations, install/update/inspect/remove flow, and explicit exclusion of user credentials, memories, sessions, and local state from distributed content.
- **FR-005**: OpenClaw setup MUST support its documented plugin model: a plugin package with manifest metadata, compatibility expectations, focused SDK entry points, tool or hook registration where needed, and opt-in handling for optional or side-effectful capabilities.
- **FR-006**: Claude setup MUST preserve the existing Claude tutor baseline while supporting documented plugin packaging: plugin manifest metadata, namespaced skills, local plugin loading for testing, plugin reload behavior, and component checks for skills, agents, and hooks where applicable.
- **FR-007**: Codex setup MUST support documented Codex plugin packaging: a plugin manifest, skill directory, local or repo-scoped marketplace listing, local verification path, and workspace-sharing boundaries where applicable.
- **FR-008**: System MUST define one host-capability profile per included host covering text support, lifecycle availability, setup entry point, update behavior, and unsupported capabilities.
- **FR-009**: System MUST provide or reuse a conformance kit that verifies every supported host adapter against the same learner-visible tutor contracts, capability reporting, lifecycle behavior, error behavior, and local data ownership expectations.
- **FR-010**: System MUST keep pedagogy, scheduling, feedback semantics, progress calculation, and local learner data independent from host-specific setup code.
- **FR-011**: System MUST support hosts without Claude-style lifecycle hooks through an explicit alternate boot-context trigger.
- **FR-012**: System MUST assign each included host implementation to a separate primary subagent: one for Hermes, one for OpenClaw, one for Claude, and one for Codex.
- **FR-013**: Each host subagent MUST report the official source sections used, setup decisions made, changed files, verification commands or manual checks performed, failures found, and unresolved blockers.
- **FR-013a**: Before each host subagent starts implementation, the main maintainer MUST provide a full context package containing the active spec, relevant roadmap and constitution constraints, official source URLs, host setup profile contract location, shared conformance expectations, verification/reporting requirements, and existing host-adapter baseline notes.
- **FR-013b**: Each host subagent MUST create and own its host setup profile contract under `specs/006-agent-adapter-setup/contracts/host-setup-profiles/` as part of its implementation slice.
- **FR-014**: The main maintainer MUST review every subagent-reported changed file and resolve shared-contract conflicts before marking the feature ready.
- **FR-015**: System MUST verify each included host through a final manual provider install test covering install, launch, capability check, representative tutor flow, update or reload, and user-data preservation checks.
- **FR-015a**: Representative tutor-flow verification MUST include every Phase 5 text flow: reading comprehension, guided lesson, transcript drill, vocab drill, free-writing feedback, and progress check.
- **FR-016**: System MUST surface host-specific setup failures with actionable messages that identify the failed host, missing prerequisite, invalid configuration, or unsupported capability.
- **FR-017**: System MUST avoid packaging, copying, logging, or publishing user secrets, learner memories, conversation sessions, SQLite state, logs, or local-only configuration as part of any host distribution.
- **FR-018**: System MUST document any host setup limitation that prevents feature parity and gate affected tutor flows on declared capabilities.
- **FR-018a**: Any representative tutor-flow failure MUST block feature readiness unless the host capability profile documents the limitation, gates the affected flow, and the manual provider install report records the skipped flow.
- **FR-019**: System MUST NOT add audio modalities, image modalities, graphical dashboards, cloud sync, multi-user behavior, bundled curricula, gamification, FSRS, new learner data stores, or Antigravity support as part of this feature.

### Key Entities *(include if feature involves data)*

- **Host Setup Target**: One supported host in this feature, including display name, official source URL, setup package model, prerequisites, and verification expectations.
- **Official Source Evidence**: The captured source-backed facts in versioned host setup profile contracts used to justify each host setup profile and reject unsupported assumptions.
- **Adapter Capability Profile**: A host declaration of available input/output modalities, lifecycle behavior, setup entry point, update behavior, and unsupported features.
- **Setup Package**: The distributable or loadable host-specific package that lets a user install and run the tutor on a target host.
- **Subagent Implementation Slice**: One host-specific implementation assignment with a main-maintainer context package, owned host setup profile contract, source usage, changed-file report, verification evidence, and blocker notes.
- **Conformance Run**: A verification record showing one host adapter passed common tutor contracts, capability checks, lifecycle checks, and data ownership checks.
- **Manual Provider Install Report**: Evidence that the maintainer manually installed, launched, updated or reloaded, and inspected the tutor setup for one supported host.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: Host adapters, adapter capability contracts, lifecycle boot-context routing, setup and distribution packaging, plugin or profile metadata, conformance tests, integration tests, and documentation. Pedagogy core, scheduling, feedback semantics, progress calculations, and DAL ownership must remain host-independent.
- **Data Ownership**: Existing local SQLite remains the source of truth for learner events, mistake events, feedback-derived signals, sessions, and progress inputs. YAML remains limited to human-editable learner profile and preferences. Host setup packages may include metadata and defaults, but must exclude secrets, learner memories, conversation sessions, SQLite state, logs, and machine-local overrides.
- **Contract Surfaces**: Adapter Protocol, host capability profile, lifecycle availability contract, boot-context trigger contract, versioned host setup profile contracts, conformance-kit expectations, CLI JSON used by host adapters, plugin/profile manifest metadata, and setup verification reports.
- **Required Validation**: Official-source evidence review; main-maintainer context package review before each host subagent starts; one subagent pressure/implementation report per included host; main-agent changed-file review; unit and contract tests for capability and lifecycle contracts; conformance-kit tests for each host; integration tests for representative tutor flows; final manual provider install/update checks; data ownership checks proving user secrets and learner state are not distributed.
- **Skill Creation**: No new learner-facing tutor skill is planned by default. If any `SKILL.md` is created or updated for host setup, the work must follow the constitution skill gate: local writing-skills helper, required external references, assigned subagent pressure evidence, activation/description review, and main-agent changed-file review.
- **Scope Guardrails**: This feature is limited to Hermes, OpenClaw, Claude, and Codex setup plus host portability verification. It excludes Antigravity, audio, images, dashboards, GUI/web analytics, cloud sync, multi-user behavior, new learner persistence, new scheduling algorithms, bundled curriculum, gamification, and pedagogy rewrites.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 4 of 4 included hosts have a completed versioned host setup profile contract with official source URL, setup package model, prerequisites, update behavior, user-owned data boundary, and verification expectations.
- **SC-002**: 4 of 4 included host implementations are assigned to separate primary subagents after receiving a main-maintainer context package, and each subagent report includes source usage, changed files, setup decisions, verification evidence, failures, blockers, and the owned host setup profile contract path.
- **SC-003**: 4 of 4 included hosts pass the shared conformance kit for capability reporting, lifecycle behavior, supported representative tutor flows, learner-visible error behavior, and local data ownership; any skipped representative flow has a documented capability-gated reason.
- **SC-004**: 4 of 4 included hosts complete final manual provider install verification covering install, launch, capability check, supported representative tutor flows, update or reload, and user-data preservation; any skipped representative flow is recorded in the host's manual provider install report.
- **SC-005**: 100% of representative tutor contract fixtures for supported reading comprehension, guided lesson, transcript drill, vocab drill, free-writing feedback, and progress check produce host-independent feedback, progress, and local data behavior across all included hosts.
- **SC-006**: 0 Antigravity files, tasks, adapters, docs, tests, or setup deliverables are added during this feature.
- **SC-007**: 0 user secrets, learner memories, conversation sessions, SQLite state, logs, or machine-local overrides are included in distributed host setup packages in packaging verification.
- **SC-008**: 100% of host-specific setup failures in edge-case tests identify the affected host and the missing prerequisite, invalid configuration, or unsupported capability.
- **SC-009**: The existing Claude tutor baseline remains passing in 100% of pre-existing Claude adapter and tutor-flow regression tests after the new host setup work.
- **SC-010**: A dogfood report demonstrates a successful tutor launch and all supported representative tutor flows on Hermes, OpenClaw, Claude, and Codex before the feature is marked complete, with any skipped flow documented as capability-gated.

## Assumptions

- "Hermess" in the request refers to Hermes Agent from Nous Research.
- Official setup documentation reviewed for this specification: Hermes profile distributions, OpenClaw plugin building, Claude Code plugins, and Codex plugin build docs.
- Phase 5 text-modality work is the latest completed baseline, and the host-capability/conformance layer may be introduced or completed as part of this feature if it is not already available.
- Claude already has a working baseline; this feature verifies and packages it as the reference host while adding equivalent setup paths for Hermes, OpenClaw, and Codex.
- All included hosts are expected to support at least text-based tutor flows. Audio and image capability are not required for this feature.
- Host setup packages should prefer the host's documented distribution model over a generic archive or manual copy workflow.
- Required user secrets or credentials are provided by the installer and are never committed, packaged, or copied from the author environment.
- Each host-specific implementation slice will be planned and executed independently, but shared capability contracts and conformance tests remain centrally reviewed.

## Amendment — Phase 8 Adapter Expansion (2026-05-23)

**Status:** Scope guardrail SC-006 and the §Scope Guardrails Antigravity exclusion are **superseded** by Phase 8 (`specs/008-qa-harness-agent/`). The spec body above is preserved as the spec-006-shipped baseline; this amendment records the in-scope additions handed to Phase 8 and required by Constitution v1.3.0 (Principle V).

**Authority:** Constitution v1.3.0 §V (v1 host set now includes Antigravity and OpenCode); Phase 8 design `specs/008-qa-harness-agent/design.md` §Adapter expansion; ROADMAP Phase 8.

**Net changes vs. spec-006-shipped:**

| Surface | spec-006-shipped | Phase 8 amendment |
|---|---|---|
| `HostId` enum | `{claude, codex, hermes, openclaw}`; antigravity rejected at schema layer | Add `antigravity` and `opencode`; remove the antigravity reject |
| `AdapterCapabilityProfile` coverage | 4 hosts | 6 hosts (adds `agy`, `opencode`) |
| `adapters/registry.py` | 4 entries | 6 entries (`agy`, `opencode` registered) |
| Plugin artifacts | `claude-plugin/` (via `.claude/`), `.codex-plugin/`, `hermes-profile/`, `openclaw-plugin/` | + `agy-plugin/`, `opencode-plugin/` (mirror `.codex-plugin/` shape) |
| Manual install reports | 4 hosts under `manual-install-reports/` | + `manual-install-reports/agy.md`, `manual-install-reports/opencode.md` |
| Capability profile contracts | `contracts/host-setup-profiles/{claude,codex,hermes,openclaw}.md` | + `contracts/host-setup-profiles/agy.md`, `contracts/host-setup-profiles/opencode.md` |
| Packaging-privacy coverage | `tests/packaging/test_host_setup_profiles.py::test_no_antigravity_artifacts` (negative) | Delete the negative test; replace with positive packaging-privacy coverage for `agy-plugin/` and `opencode-plugin/` mirroring the four existing hosts |
| SC-006 | "0 Antigravity files … added" | **Superseded.** Replaced by Phase 8 SC: `agy` and `opencode` ship with the same capability/lifecycle/conformance/packaging-privacy gates green as the four spec-006 hosts |
| Scope Guardrails | Excludes Antigravity | Antigravity is in scope as of Phase 8; OpenCode is in scope as of Phase 8 |

**Unchanged by this amendment:**

- Constitution Principles I–IV and VI–X — adapters added under existing contracts, no new persistence path, no pedagogy change, hook-free lifecycle (Principle IX) applies unchanged.
- Conformance kit (`tests/adapter_contract/test_conformance_kit.py`) — new hosts pass the existing kit; no kit changes implied.
- Capability axes — both new hosts declare `text_support` only; audio/image stay locked unsupported (Phase 9).
- Lifecycle fields — `lifecycle_start=first_message`, `lifecycle_end=not_available`, `persistence_mode=incremental_checkpoint`, `boot_context_trigger=first_tutor_message` for both new hosts.
- Data-ownership boundary — `agy-plugin/` and `opencode-plugin/` MUST contain zero user secrets, learner memories, conversation sessions, SQLite state, logs, or machine-local overrides; enforced by the replacement packaging-privacy test.

**Out of scope of this amendment (still deferred):**

- Audio / image capability for any host (Phase 9).
- QA harness driver implementations for `agy` and `opencode` — owned by Phase 8 `tests/qa/drivers/` work, tracked under `specs/008-qa-harness-agent/`, not under spec 006.
- Re-running spec-006 manual provider install verification for the four original hosts; this amendment does not invalidate prior dogfood evidence.

**Acceptance:** Phase 8 plan MUST cite this amendment in its Constitution Check, MUST land all rows in the table above before declaring the adapter-expansion exit gate met, and MUST keep all spec-006 contract / capability / lifecycle / conformance / packaging-privacy tests green for `claude`, `codex`, `hermes`, `openclaw` while extending them to `agy` and `opencode`.

