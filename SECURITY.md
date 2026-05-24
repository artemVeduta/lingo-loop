# Security Policy

## Supported versions

This project is currently in pre-1.0 development. Only the latest `0.x` minor
release line receives security fixes. Once `1.0` ships, the two most recent
minor lines will be supported.

| Version | Supported          |
|---------|--------------------|
| `0.x`   | :white_check_mark: |
| `< 0.1` | :x:                |

## Reporting a vulnerability

Please **do not open public GitHub issues** for security vulnerabilities.

Report vulnerabilities privately via GitHub Security Advisories:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability**.
3. Fill in the form with as much detail as possible (reproduction, affected
   versions, impact).

If GitHub Security Advisories are unavailable to you, email the maintainer at
`veduta.artem20@gmail.com` with subject prefix `[security]`.

## Response timeline

The maintainer will acknowledge new reports on a best-effort basis **within
14 days**. This is a solo-maintained project; complex issues may take longer
to triage and fix. You will receive updates as the investigation progresses.

## Scope

In scope:

- The `tutor` CLI shipped from this repository.
- The four host integrations as shipped in this repository:
  `.claude-plugin/`, `.codex-plugin/`, `hermes-profile/`, `openclaw-plugin/`.

Out of scope:

- The host CLIs themselves (Claude Code, Codex, Hermes, OpenClaw) — report
  upstream.
- Vulnerabilities in user-supplied LLM API keys, OS-level credential stores,
  or third-party libraries (report to those projects).
- Issues that require local root or physical access to the user's machine.

## Coordinated disclosure

This project follows a coordinated-disclosure model: fixes are developed and
released privately, then the advisory is published. Reporters are credited in
the advisory unless they request otherwise.
