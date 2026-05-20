from __future__ import annotations

from typing import Protocol


class JsonCommandRunner(Protocol):
    def run_json(
        self, args: list[str], payload: dict[str, object] | None = None
    ) -> dict[str, object]:
        """Run a host-facing JSON command."""
        ...


class HookPayloadAdapter(Protocol):
    def normalize(self, payload: dict[str, object]) -> dict[str, object]:
        """Normalize host hook payload into core JSON."""
        ...
