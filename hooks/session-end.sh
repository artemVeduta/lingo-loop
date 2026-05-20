#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD="${1:-{}}"
"$ROOT/bin/tutor" session-end --json "$PAYLOAD" || true
