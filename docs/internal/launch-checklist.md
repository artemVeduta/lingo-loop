# OSS launch checklist (assets)

Every item below is **launch-blocking** for the public announcement of `lingo-loop` v0.1. They are *not* merge-blocking for the `oss-baseline` change — placeholders shipped via `<!-- TODO(oss-baseline-assets): ... -->` comments in the docs.

Internal tracking only; safe to delete once everything is filled.

## README

- [ ] `docs/assets/demo.cast` — top-level asciinema cast of a typical tutor session (referenced from README placeholder).
- [ ] `docs/assets/demo.gif` — GIF rendered from `demo.cast` via `agg` / `asciinema-agg` (the in-README visual, since GitHub strips JS).

## Per-host install docs

### Claude (`docs/install/claude.md`)
- [ ] `docs/assets/claude-plugin-enabled.png` — screenshot of the Claude `/plugin` panel showing `language-tutor` enabled.
- [ ] `docs/assets/claude-first-session.cast` — asciinema cast of the first session in Claude Code.

### Codex (`docs/install/codex.md`)
- [ ] `docs/assets/codex-plugin-enabled.png` — screenshot of the Codex marketplace/plugins pane showing `language-tutor` enabled.
- [ ] `docs/assets/codex-first-session.cast` — asciinema cast of the first Codex tutor session.

### Hermes (`docs/install/hermes.md`)
- [ ] `docs/assets/hermes-profile-installed.png` — screenshot of `hermes profile list` output (or UI listing) showing `language-tutor`.
- [ ] `docs/assets/hermes-first-session.cast` — asciinema cast of `hermes run language-tutor` first session.

### OpenClaw (`docs/install/openclaw.md`)
- [ ] `docs/assets/openclaw-plugin-enabled.png` — screenshot of the OpenClaw plugins panel showing `@language-tutor/openclaw-plugin` enabled.
- [ ] `docs/assets/openclaw-first-session.cast` — asciinema cast of the first OpenClaw tutor session.

## Verification dates

Each install doc carries a `Last verified: YYYY-MM-DD` line. Refresh on each release; a future CI check (planned in `publish-pypi`) will warn if any date is older than 90 days.

- [ ] `docs/install/claude.md` — verify against current Claude Code release, update header.
- [ ] `docs/install/codex.md` — verify against current Codex CLI release, update header.
- [ ] `docs/install/hermes.md` — verify against current Hermes release, update header.
- [ ] `docs/install/openclaw.md` — verify against current OpenClaw release, update header.

## Inline `TODO: verify` markers

Every public doc carries one or more `<!-- TODO: verify -->` markers that must be resolved before the v0.1 announcement. Each must be either confirmed (delete the marker) or fixed (update the surrounding text, then delete the marker). Track them here:

### Host-CLI install syntax (verify against each host's current release)
- [ ] `docs/install/claude.md:3` — Claude Code version pin in `Last verified:` header.
- [ ] `docs/install/claude.md:43` — exact `claude plugin install` invocation.
- [ ] `docs/install/codex.md:3` — Codex CLI version pin in `Last verified:` header.
- [ ] `docs/install/codex.md:40` — exact `codex plugin install` invocation.
- [ ] `docs/install/hermes.md:3` — Hermes version pin in `Last verified:` header.
- [ ] `docs/install/hermes.md:40` — exact `hermes profile install` syntax for git+subdir.
- [ ] `docs/install/openclaw.md:3` — OpenClaw version pin in `Last verified:` header.
- [ ] `docs/install/openclaw.md:42` — exact `openclaw plugin install` syntax.

### Configuration enum values
- [ ] `docs/configuration.md:51` — verify `review_intensity` accepted enum values.
- [ ] `docs/configuration.md:52` — verify `feedback_verbosity` accepted enum values.

A CI guard (added in `.github/workflows/ci.yml`) already fails the build if `rtk` or `Spec N` references leak into public docs; once the items above are resolved, consider extending the guard to fail on any remaining `<!-- TODO: verify -->` marker as a release gate.

## Public-issue mirror

Once the repo announcement is imminent, mirror this checklist into a pinned GitHub issue titled **"Launch-blocking assets"** (per `tasks.md` 8.4) so external contributors can claim items.
