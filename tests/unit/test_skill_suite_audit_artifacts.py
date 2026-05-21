from __future__ import annotations

from pathlib import Path

SPEC = Path("specs/005-text-modalities")
HELPER_PATH = (
    "/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/"
    "superpowers/5.1.0/skills/writing-skills"
)


def test_rewrite_evidence_names_helper_and_blocked_rule() -> None:
    text = (SPEC / "skill-rewrite-evidence.md").read_text(encoding="utf-8")
    assert HELPER_PATH in text
    assert "blocked" in text.lower()
    for field in ("RED", "GREEN", "REFACTOR", "changed file", "main-agent"):
        assert field.lower() in text.lower(), field


def test_coherence_audit_has_decision_fields() -> None:
    text = (SPEC / "skill-suite-coherence-audit.md").read_text(encoding="utf-8").lower()
    for field in (
        "trigger_overlap",
        "convention_drift",
        "duplicated_pedagogy",
        "decision",
        "transcript",
    ):
        assert field in text, field


def test_inventory_records_compliance_decisions() -> None:
    text = (SPEC / "skill-inventory.md").read_text(encoding="utf-8")
    assert "compliant" in text
    assert "not_in_scope" in text
