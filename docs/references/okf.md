---
type: Reference
title: Open Knowledge Format (OKF) v0.1
description: Summary of the OKF v0.1 draft spec that this bundle conforms to.
resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
timestamp: 2026-06-22
---

# Open Knowledge Format (OKF) v0.1

OKF is a plain-markdown knowledge format. A **bundle** is a directory tree of `.md`
files (the unit of distribution). A **concept** is one markdown file = YAML frontmatter +
body. A concept's ID is its bundle-relative path minus `.md` (no normalization).

## Conformance (§9) — the entire hard bar

1. Every non-reserved `.md` file has a parseable YAML frontmatter block.
2. Every frontmatter block has a non-empty `type` field.
3. Reserved files (`index.md`, `log.md`) follow their structure (§6, §7) when present.

Everything else is soft guidance. Consumers MUST tolerate: missing optional fields,
unknown `type` values, unknown extra keys, broken cross-links, and missing `index.md`.

## Reserved files

- `index.md` (§6): progressive-disclosure link lists. Frontmatter is permitted in exactly
  one place — the bundle-root `index.md`, solely to declare `okf_version: "0.1"`.
- `log.md` (§7): date-grouped change history, ISO `## YYYY-MM-DD` headings, newest first.

## Frontmatter (§4.1)

`type` is REQUIRED. `title`, `description`, `resource`, `tags`, `timestamp` are
recommended. Any other key is allowed; consumers preserve unknown keys.

## Linking (§5)

Absolute bundle-relative (`/path.md`) or relative (`./other.md`) markdown links. There
are no typed relations — relationship kind lives in prose. Broken links are not errors.

## Tooling

There is no manifest, schema registry, or required validator. "If you can `cat` a file,
you can read OKF; if you can `git clone` a repo, you can ship it." This repo's
`npm run docs:validate` is an optional, advisory backstop, not an OKF requirement.

# Citations

- OKF SPEC.md v0.1 (Draft) — `GoogleCloudPlatform/knowledge-catalog`, `okf/SPEC.md`.
