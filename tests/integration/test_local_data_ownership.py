from __future__ import annotations

import json
from pathlib import Path

from language_tutor.dal.paths import resolve_paths
from language_tutor.dal.sqlite_store import connect
from tests.conftest import invoke_json
from tests.fixtures.text_modalities.builders import record_payload, transcript_candidate

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}'
)


def test_setup_does_not_create_history(runner, tutor_home: Path) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    assert not (tutor_home / "state" / "history.sqlite3").exists()


def test_transcript_uses_reading_skill_and_no_new_table(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])
    tables_before = _table_names()
    exercise = invoke_json(
        runner, ["reading", "start", "--json", json.dumps({"mode": "transcript", "candidate": transcript_candidate()})]
    )
    assert exercise["exercise_id"].startswith("transcript_")
    result = invoke_json(
        runner,
        ["reading", "record", "--json", json.dumps(record_payload(exercise["exercise_id"], modality="transcript"))],
    )
    assert result["answer_event"]["skill"] == "reading"
    assert _table_names() == tables_before  # no new runtime table

    conn = connect(resolve_paths().database_path)
    try:
        row = conn.execute(
            "SELECT skill FROM answer_events WHERE prompt_ref = ?", (exercise["exercise_id"],)
        ).fetchone()
        assert row["skill"] == "reading"
    finally:
        conn.close()


def _table_names() -> set[str]:
    conn = connect(resolve_paths().database_path)
    try:
        return {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


# --- US3/US4: host packages never carry user-owned data -------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOTS = (
    "openclaw-plugin",
    "hermes-profile",
    "skills",
)


def test_host_packages_carry_no_user_owned_state() -> None:
    offenders: list[str] = []
    forbidden_suffix = (".env", ".sqlite", ".sqlite3", ".db", ".db-wal", ".db-shm", ".log")
    forbidden_dirs = {"memories", "sessions", "logs", "caches", "local"}
    for rel in PACKAGE_ROOTS:
        root = REPO_ROOT / rel
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if "node_modules" in path.parts or "__pycache__" in path.parts:
                continue
            if path.is_file() and path.suffix in forbidden_suffix:
                offenders.append(str(path.relative_to(REPO_ROOT)))
            if path.is_dir() and path.name in forbidden_dirs:
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"user-owned state found in host packages: {offenders}"


def test_host_profiles_declare_user_owned_boundaries() -> None:
    from language_tutor.adapters.base import load_host_setup_profile

    profile_dir = REPO_ROOT / "specs/006-agent-adapter-setup/contracts/host-setup-profiles"
    for host in ("hermes", "openclaw", "claude", "codex"):
        path = profile_dir / f"{host}.md"
        if not path.exists():
            continue
        contract = load_host_setup_profile(str(path))
        joined = " ".join(contract.user_owned_boundaries).lower()
        for token in ("secrets", "memories", "sessions"):
            assert token in joined, f"{host} profile boundary missing {token}"
