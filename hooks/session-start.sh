#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOT="$("$ROOT/bin/tutor" boot-context --json)"
"$ROOT/bin/tutor" render boot-context --json "$BOOT"
