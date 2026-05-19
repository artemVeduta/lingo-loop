# Language Tutor AI Core Architecture Design

## 1. System Goals & Requirements
A cross-platform AI language tutor system that runs on Claude, Codex, OpenClaw, and Hermess. 
* **Platform Agnostic:** Core teaching logic, spaced repetition algorithms, and session management are completely decoupled from the LLM host.
* **Context Efficiency:** Bootstrapping a session loads only highly relevant user context (`get_boot_context`) to conserve context tokens and ensure low latency.
* **Consistent Learner Experience:** The formatting of feedback, error tracking, and severity mapping is identical regardless of the AI engine running the session.
* **Hybrid State Management:** Human-readable configuration (profiles, preferences) is stored in YAML. Structured transaction data (drill histories, mistake patterns, spaced-repetition intervals) resides in SQLite.
* **Shared Core Language:** Python is the primary language for the Shared Core Engine, Host Adapters, and Data Access Layer due to its native integration with OpenClaw/Hermess and built-in `sqlite3` library.

## 2. Core Architectural Model
The system uses an explicit layered architecture to isolate platform-specific integrations from the learning engine.

* **Host Adapters / Hooks Layer:** Normalizes input/output formats for each LLM provider. Implements plugin setups for OpenClaw, profile distributions for Hermess, and local CLI hook stubs for Claude/Codex. Integrates optional native memory where applicable.
* **Shared Core Engine (Python):** Executes the interactive flow and structures prompts/feedback. Evaluates exercises, handles spaced repetition math, and formats standardized feedback tokens (✅, ❌, severity emojis).
* **Data Access Layer (DAL):** Abstracts data persistence. Exposes generic interfaces like `save_profile()` or `record_answer_event()` to interact seamlessly with local YAML configurations and the SQLite database.

## 3. High-Level Lifecycle Flow
Every interactive skill follows a standardized execution lifecycle with specific hooks:

1.  `get_boot_context()`: Loads profile, constraints, and summary metrics from YAML/DB.
2.  `get_due_reviews()`: Retrieves Spaced-Repetition items due for drill.
3.  `search_weak_patterns()`: Scans historical error tags for targeted practice.
4.  **Interactive Loop:**
    * Present exercise and await user answer.
    * `record_answer(event)`: Processes response, evaluating grammar, register, vocabulary, etc.
    * `tutor-feedback`: Renders a standardized structure layout with immediate feedback to the user.
5.  **Session End Triggered:**
    * `tutor-session-analyzer(summary)`: Parses session logs for severity metrics, tallies new error tags, and calculates pattern drift.
    * `update_state_after_session()`: Commits calculated summary metrics to the database, updates streak data/session counts, and writes the `last_session_timestamp`.
    * `end_session()`: Destroys temporary run state, flushes text buffers, and safely closes SQLite file connections.

## 4. Phased Implementation Roadmap
This project will be implemented iteratively across targeted sub-projects:

* **Phase 0: Project Monorepo Setup & Provider Hooks**
    * Initialize core repository structure.
    * Scaffold Hermess `profile-distributions`, OpenClaw plugin schemas, and Claude/Codex system prompts.
    * Write a unified `README.md` detailing multi-platform installation and hook-binding.
* **Phase 1: Foundations & Adapters** * Implement the Data Access Layer (DAL), SQLite initialization scripts, YAML loaders, and functional Python Host Adapters.
* **Phase 2: Onboarding & Profile** * Develop `tutor-setup` for interactive `/fluent-setup` registration and `tutor-progress` for analytics viewing.
* **Phase 3: Core Mechanics & Vocabulary** * Build `tutor-vocab`, spaced-repetition math, `tutor-feedback` standard markdown rendering, `tutor-session-analyzer`, and session-end persistence hooks.
* **Phase 4: Production Skills** * Develop `tutor-writing`, `tutor-reading`, `tutor-listening`, and `tutor-speaking` with targeted practice modalities and prompt structures.
* **Phase 5: Compound Sessions** * Build `tutor-lesson` to sequence multiple skills into long-form structured learning sessions.