---
paths:
  - "src/**/*.py"
---

# Keep docs in sync with source

- You are editing source. Check whether the mirrored `docs/…` concept needs
  updating — a `Specification` if behaviour/mechanics changed, a `Decision`
  amendment if an architectural choice changed.
- The docs bundle is the source of truth; see `docs/conventions/documentation.md`.
- This is advisory, never blocking. Not every file has docs yet — if no matching
  concept exists, there's nothing to update.
