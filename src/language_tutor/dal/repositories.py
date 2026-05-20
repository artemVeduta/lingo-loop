from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime

from language_tutor.dal.sqlite_store import transaction
from language_tutor.schemas import (
    AnswerEvent,
    CostEventInput,
    ErrorSpan,
    FeedbackEnvelope,
    SessionAnalysis,
    VocabularyAnswerResult,
    VocabularyItem,
    VocabularyItemState,
    VocabularyReview,
)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def normalize_key(target_language: str, lemma: str | None, prompt: str) -> str:
    basis = lemma or prompt
    return f"{target_language.strip().lower()}:{' '.join(basis.lower().split())}"


class TutorRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def upsert_vocabulary_item(self, item: VocabularyItem) -> str:
        dedupe = normalize_key(item.target_language, item.lemma, item.prompt)
        current = self.conn.execute(
            "SELECT id FROM vocabulary_items WHERE dedupe_key = ?", (dedupe,)
        ).fetchone()
        if current:
            return str(current["id"])
        state = item.state
        self.conn.execute(
            """
            INSERT INTO vocabulary_items(
              id, target_language, prompt, lemma, accepted_answers_json, hint, tags_json, state,
              ease_factor, repetition_count, interval_days, due_at, created_at, updated_at, dedupe_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.target_language,
                item.prompt,
                item.lemma,
                json.dumps(item.accepted_answers, ensure_ascii=False),
                item.hint,
                json.dumps(item.tags, ensure_ascii=False),
                state.state,
                state.ease_factor,
                state.repetition_count,
                state.interval_days,
                state.due_at.isoformat(),
                now_iso(),
                now_iso(),
                dedupe,
            ),
        )
        return item.id

    def due_vocabulary(self, limit: int, now: datetime) -> list[VocabularyItem]:
        rows = self.conn.execute(
            "SELECT * FROM vocabulary_items WHERE due_at <= ? ORDER BY due_at, created_at LIMIT ?",
            (now.isoformat(), limit),
        ).fetchall()
        return [self._row_to_vocab(row) for row in rows]

    def get_vocabulary_item(self, item_id: str) -> VocabularyItem:
        row = self.conn.execute(
            "SELECT * FROM vocabulary_items WHERE id = ?", (item_id,)
        ).fetchone()
        if row is None:
            raise KeyError(item_id)
        return self._row_to_vocab(row)

    def record_vocab_answer(
        self,
        *,
        item: VocabularyItem,
        session_id: str,
        answer: str,
        idempotency_key: str,
        feedback: FeedbackEnvelope,
        previous_state: VocabularyItemState,
        next_state: VocabularyItemState,
        quality: int,
    ) -> VocabularyAnswerResult:
        existing = self.conn.execute(
            """
            SELECT ae.*, vr.id AS review_id, vr.verdict, vr.quality, vr.previous_state_json, vr.next_state_json, vr.reviewed_at
            FROM answer_events ae
            JOIN vocabulary_reviews vr ON vr.answer_event_id = ae.id
            WHERE ae.idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()
        if existing:
            event = AnswerEvent(
                id=str(existing["id"]),
                session_id=str(existing["session_id"]),
                skill="vocab",
                prompt_ref=str(existing["prompt_ref"]),
                learner_answer=str(existing["learner_answer"]),
                outcome=str(existing["outcome"]),
                feedback_envelope=FeedbackEnvelope.model_validate_json(
                    existing["feedback_envelope_json"]
                ),
                recorded_at=datetime.fromisoformat(str(existing["recorded_at"])),
            )
            review = VocabularyReview(
                id=str(existing["review_id"]),
                session_id=session_id,
                vocabulary_item_id=item.id,
                answer_event_id=event.id,
                verdict=existing["verdict"],
                quality=int(existing["quality"]),
                previous_state=VocabularyItemState.model_validate_json(
                    existing["previous_state_json"]
                ),
                next_state=VocabularyItemState.model_validate_json(existing["next_state_json"]),
                reviewed_at=datetime.fromisoformat(str(existing["reviewed_at"])),
            )
            return VocabularyAnswerResult(
                feedback=event.feedback_envelope or feedback,
                answer_event=event,
                review=review,
                duplicate=True,
            )

        with transaction(self.conn):
            event_id = new_id("ans")
            review_id = new_id("rev")
            recorded_at = now_iso()
            self.conn.execute(
                """
                INSERT INTO answer_events(id, idempotency_key, session_id, skill, prompt_ref, learner_answer, outcome, feedback_envelope_json, recorded_at)
                VALUES (?, ?, ?, 'vocab', ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    idempotency_key,
                    session_id,
                    item.id,
                    answer,
                    feedback.verdict,
                    feedback.model_dump_json(),
                    recorded_at,
                ),
            )
            self.conn.execute(
                """
                INSERT INTO vocabulary_reviews(id, session_id, vocabulary_item_id, answer_event_id, verdict, quality, previous_state_json, next_state_json, reviewed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    session_id,
                    item.id,
                    event_id,
                    feedback.verdict,
                    quality,
                    previous_state.model_dump_json(),
                    next_state.model_dump_json(),
                    recorded_at,
                ),
            )
            self.conn.execute(
                """
                UPDATE vocabulary_items
                SET state = ?, ease_factor = ?, repetition_count = ?, interval_days = ?, due_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_state.state,
                    next_state.ease_factor,
                    next_state.repetition_count,
                    next_state.interval_days,
                    next_state.due_at.isoformat(),
                    recorded_at,
                    item.id,
                ),
            )
        event = AnswerEvent(
            id=event_id,
            session_id=session_id,
            skill="vocab",
            prompt_ref=item.id,
            learner_answer=answer,
            outcome=str(feedback.verdict),
            feedback_envelope=feedback,
            recorded_at=datetime.fromisoformat(recorded_at),
        )
        review = VocabularyReview(
            id=review_id,
            session_id=session_id,
            vocabulary_item_id=item.id,
            answer_event_id=event_id,
            verdict=feedback.verdict,
            quality=quality,
            previous_state=previous_state,
            next_state=next_state,
            reviewed_at=datetime.fromisoformat(recorded_at),
        )
        return VocabularyAnswerResult(feedback=feedback, answer_event=event, review=review)

    def record_writing_answer(
        self, session_id: str, prompt_id: str, answer: str, feedback: FeedbackEnvelope
    ) -> tuple[AnswerEvent, int]:
        with transaction(self.conn):
            event_id = new_id("ans")
            recorded_at = now_iso()
            self.conn.execute(
                """
                INSERT INTO answer_events(id, session_id, skill, prompt_ref, learner_answer, outcome, feedback_envelope_json, recorded_at)
                VALUES (?, ?, 'writing', ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    session_id,
                    prompt_id,
                    answer,
                    feedback.verdict,
                    feedback.model_dump_json(),
                    recorded_at,
                ),
            )
            persisted = 0
            for span in feedback.error_spans:
                if feedback.confidence == "low" and span.severity == "high":
                    continue
                self._insert_mistake(event_id, session_id, span, feedback.confidence)
                persisted += 1
        return (
            AnswerEvent(
                id=event_id,
                session_id=session_id,
                skill="writing",
                prompt_ref=prompt_id,
                learner_answer=answer,
                outcome=str(feedback.verdict),
                feedback_envelope=feedback,
                recorded_at=datetime.fromisoformat(recorded_at),
            ),
            persisted,
        )

    def _insert_mistake(
        self, event_id: str, session_id: str, span: ErrorSpan, confidence: str
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO mistake_events(id, session_id, answer_event_id, skill, span_start, span_end, span_text, severity, tag, explanation, confidence, created_at)
            VALUES (?, ?, ?, 'writing', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("mistake"),
                session_id,
                event_id,
                span.start,
                span.end,
                span.text,
                span.severity,
                span.tag,
                span.explanation,
                confidence,
                now_iso(),
            ),
        )

    def record_session_end(
        self, session_id: str, analysis: SessionAnalysis | None, costs: list[CostEventInput]
    ) -> tuple[str | None, str | None]:
        with transaction(self.conn):
            for cost in costs:
                self.conn.execute(
                    """
                    INSERT INTO cost_events(id, session_id, operation, model, input_tokens, output_tokens, cache_read_tokens, estimated_cost_usd, pricing_source, source_event_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("cost"),
                        session_id,
                        cost.operation,
                        cost.model,
                        cost.input_tokens,
                        cost.output_tokens,
                        cost.cache_read_tokens,
                        cost.estimated_cost_usd,
                        cost.pricing_source,
                        cost.source_event_id,
                        now_iso(),
                    ),
                )
            if analysis is None:
                return None, None
            summary_id = new_id("summary")
            self.conn.execute(
                """
                INSERT OR REPLACE INTO session_summaries(id, session_id, summary_for_user, summary_for_next_boot, weak_tags_json, next_focus, cost_snapshot_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary_id,
                    session_id,
                    analysis.summary_for_next_boot or "Session saved.",
                    analysis.summary_for_next_boot or "Session saved.",
                    json.dumps([str(tag) for tag in analysis.repeated_tags], ensure_ascii=False),
                    analysis.next_focus,
                    "{}",
                    now_iso(),
                ),
            )
        return summary_id, analysis.next_focus

    def latest_summary(self) -> str | None:
        row = self.conn.execute(
            "SELECT summary_for_next_boot FROM session_summaries ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return None if row is None else str(row["summary_for_next_boot"])

    def due_count(self, now: datetime) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS count FROM vocabulary_items WHERE due_at <= ?", (now.isoformat(),)
        ).fetchone()
        return int(row["count"])

    def weak_tags(self, limit: int = 5) -> list[str]:
        rows = self.conn.execute(
            "SELECT tag, COUNT(*) AS count FROM mistake_events GROUP BY tag ORDER BY count DESC, tag LIMIT ?",
            (limit,),
        ).fetchall()
        return [str(row["tag"]) for row in rows]

    def maturity_counts(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT state, COUNT(*) AS count FROM vocabulary_items GROUP BY state"
        ).fetchall()
        return {str(row["state"]): int(row["count"]) for row in rows}

    def month_cost(self, prefix: str) -> tuple[float | None, str]:
        rows = self.conn.execute(
            "SELECT estimated_cost_usd, pricing_source FROM cost_events WHERE created_at >= ?",
            (prefix,),
        ).fetchall()
        if not rows:
            return None, "unavailable"
        known = [
            float(row["estimated_cost_usd"])
            for row in rows
            if row["estimated_cost_usd"] is not None
        ]
        if len(known) == len(rows):
            return sum(known), "available"
        if known:
            return sum(known), "partial"
        return None, "unavailable"

    def answer_dates(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT recorded_at FROM answer_events ORDER BY recorded_at DESC"
        ).fetchall()
        return [str(row["recorded_at"])[:10] for row in rows]

    def _row_to_vocab(self, row: sqlite3.Row) -> VocabularyItem:
        return VocabularyItem(
            id=str(row["id"]),
            target_language=str(row["target_language"]),
            prompt=str(row["prompt"]),
            lemma=row["lemma"],
            accepted_answers=json.loads(str(row["accepted_answers_json"])),
            hint=row["hint"],
            tags=json.loads(str(row["tags_json"])),
            state=VocabularyItemState(
                state=row["state"],
                ease_factor=float(row["ease_factor"]),
                repetition_count=int(row["repetition_count"]),
                interval_days=int(row["interval_days"]),
                due_at=datetime.fromisoformat(str(row["due_at"])),
            ),
        )

    def seed_default_vocabulary(self, target_language: str) -> None:
        defaults = [
            VocabularyItem(
                id=new_id("vocab"),
                target_language=target_language,
                prompt="hello",
                lemma="привіт",
                accepted_answers=["привіт", "privit"],
                hint="greeting",
            ),
            VocabularyItem(
                id=new_id("vocab"),
                target_language=target_language,
                prompt="thank you",
                lemma="дякую",
                accepted_answers=["дякую", "diakuiu", "dyakuyu"],
                hint="thanks",
            ),
        ]
        for item in defaults:
            self.upsert_vocabulary_item(item)
