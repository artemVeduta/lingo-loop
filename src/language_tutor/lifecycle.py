from __future__ import annotations

from language_tutor.dal.repositories import TutorRepository
from language_tutor.schemas import SessionEndInput, SessionEndResult


def end_session(repo: TutorRepository, payload: SessionEndInput) -> SessionEndResult:
    summary_id, next_focus = repo.record_session_end(
        payload.session_id, payload.analysis, payload.costs
    )
    if summary_id is None:
        return SessionEndResult(session_id=payload.session_id, status="pending")
    return SessionEndResult(
        session_id=payload.session_id,
        status="complete",
        summary_id=summary_id,
        next_focus=next_focus,
    )
