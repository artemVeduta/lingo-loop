from __future__ import annotations

from language_tutor.boot_context import build_boot_context, render_boot_context
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.schemas import LearnerPreferences, LearnerProfile


def test_boot_context_bounded(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        context = build_boot_context(
            repo, LearnerProfile(native_language="en", target_language="uk"), LearnerPreferences()
        )
        rendered = render_boot_context(context)
        assert "First session guidance" in rendered
        assert len(rendered) <= 6000
        assert len(context.sections) <= 8
    finally:
        conn.close()
