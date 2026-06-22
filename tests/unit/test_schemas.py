from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from language_tutor.schemas import (
    AnswerEvent,
    BookList,
    BookListEntry,
    BookLog,
    BookLogEntry,
    BookLookupResult,
    BookRecordInput,
    BookSession,
    FeedbackEnvelope,
    LearnerPreferences,
    LearnerProfile,
    PracticeTotals,
    ProgressMarkdownExport,
    ProgressReport,
    ProgressReportRequest,
    SelectionPolicy,
    SelectionReason,
    TextModalityRecordInput,
    TextModalityResult,
    TextTrend,
    ValidatedTextExercise,
    VocabularyCardDefinition,
    VocabularyDrillRequest,
    VocabularyItem,
    VocabularySessionPlan,
    WeakTagSignal,
    WeakTagSourceCounts,
    export_json_schemas,
)


def test_profile_requires_languages() -> None:
    profile = LearnerProfile(native_language="en", target_language="uk")
    assert profile.level_target == "A1"


def test_json_schema_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    schema = json.loads((tmp_path / "feedback_envelope.schema.json").read_text())
    assert schema["title"] == FeedbackEnvelope.__name__
    assert (tmp_path / "vocabulary_card_definition.schema.json").exists()
    assert (tmp_path / "vocabulary_import_summary.schema.json").exists()
    assert (tmp_path / "vocabulary_session_plan.schema.json").exists()
    assert (tmp_path / "weak_tag_signal.schema.json").exists()
    assert (tmp_path / "selection_reason.schema.json").exists()
    assert (tmp_path / "vocabulary_review_history.schema.json").exists()
    assert (tmp_path / "progress_request.schema.json").exists()
    assert (tmp_path / "progress_report.schema.json").exists()
    assert (tmp_path / "progress_markdown_export.schema.json").exists()


def test_text_modality_schema_mirrors_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    for filename, title in (
        ("text_modality_result.schema.json", TextModalityResult.__name__),
        ("text_modality_record.schema.json", TextModalityRecordInput.__name__),
        ("reading_exercise.schema.json", ValidatedTextExercise.__name__),
        ("reading_result.schema.json", TextModalityResult.__name__),
        ("lesson_exercise.schema.json", ValidatedTextExercise.__name__),
        ("lesson_result.schema.json", TextModalityResult.__name__),
        ("transcript_drill.schema.json", ValidatedTextExercise.__name__),
    ):
        schema = json.loads((tmp_path / filename).read_text())
        assert schema["title"] == title


def test_book_schema_mirrors_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    for filename, title in (
        ("book_record.schema.json", BookRecordInput.__name__),
        ("book_session.schema.json", BookSession.__name__),
        ("book_lookup_result.schema.json", BookLookupResult.__name__),
        ("book_log.schema.json", BookLog.__name__),
        ("book_list.schema.json", BookList.__name__),
    ):
        schema = json.loads((tmp_path / filename).read_text())
        assert schema["title"] == title


def test_answer_event_accepts_text_modality_skills() -> None:
    for skill in ("vocab", "writing", "reading", "lesson"):
        event = AnswerEvent(
            id="ans_1",
            session_id="s1",
            skill=skill,  # type: ignore[arg-type]
            prompt_ref="reading_x",
            learner_answer="a",
            outcome="partial",
        )
        assert event.skill == skill


def test_practice_totals_include_text_modalities() -> None:
    totals = PracticeTotals(reading_answers=2, lesson_answers=1, transcript_drills=3)
    assert totals.reading_answers == 2
    assert totals.lesson_answers == 1
    assert totals.transcript_drills == 3
    assert PracticeTotals().reading_answers == 0


def test_text_modality_result_embeds_unchanged_feedback() -> None:
    result = TextModalityResult.model_validate(
        {
            "modality": "reading",
            "exercise_id": "reading_x",
            "session_id": "default",
            "response_status": "completed",
            "feedback": {"verdict": "partial"},
            "score_metadata": {"questions_total": 2, "questions_correct": 1},
        }
    )
    assert result.feedback.verdict == "partial"
    assert result.answer_event is None
    assert "text_only" in result.scope_guardrails


def test_vocabulary_item_phase2_defaults() -> None:
    item = VocabularyItem(
        id="vocab_1",
        target_language="uk",
        prompt="hello",
        accepted_answers=["привіт"],
    )
    assert item.card_type == "standard"
    assert item.notes == []
    assert item.sources == []


def test_card_definition_rejects_empty_metadata() -> None:
    with pytest.raises(ValidationError):
        VocabularyCardDefinition.model_validate(
            {
                "target": "привіт",
                "prompt": "hello",
                "accepted_answers": ["привіт"],
                "tags": [""],
            }
        )


def test_card_definition_validates_cloze_marker_count() -> None:
    card = VocabularyCardDefinition.model_validate(
        {
            "card_type": "cloze",
            "target": "привіт",
            "prompt": "{{answer}} is a greeting.",
            "accepted_answers": ["привіт"],
        }
    )
    assert card.card_type == "cloze"
    with pytest.raises(ValidationError):
        VocabularyCardDefinition.model_validate(
            {
                "card_type": "cloze",
                "target": "привіт",
                "prompt": "{{answer}} and {{answer}}",
                "accepted_answers": ["привіт"],
            }
        )


def test_drill_request_rejects_empty_tags() -> None:
    with pytest.raises(ValidationError):
        VocabularyDrillRequest.model_validate({"tags": []})


def test_smarter_engine_schema_contracts() -> None:
    signal = WeakTagSignal(
        tag="case",
        session_count=2,
        latest_seen_at="2026-05-21T12:00:00Z",
        priority_rank=1,
        source_counts=WeakTagSourceCounts(mistake_events=2, low_quality_reviews=1),
    )
    reason = SelectionReason(
        item_id="vocab_1",
        rank=1,
        bucket="due_today",
        reasons=["due", "weak_tag_match"],
        matched_weak_tags=["case"],
        due_at="2026-05-21T12:00:00Z",
    )
    plan = VocabularySessionPlan(
        items=[
            VocabularyItem(
                id="vocab_1",
                target_language="uk",
                prompt="book",
                accepted_answers=["книга"],
            )
        ],
        requested_count=90,
        effective_count=60,
        active_weak_tags=[signal],
        selection_reasons=[reason],
        selection_policy=SelectionPolicy(intensity="heavy", reserved_non_weak_due_slot=True),
    )
    assert plan.active_weak_tags[0].source_counts.low_quality_reviews == 1
    assert plan.selection_reasons[0].item_id == "vocab_1"
    assert plan.selection_policy.intensity == "heavy"


def test_review_intensity_validation() -> None:
    assert LearnerPreferences().review_intensity == "normal"
    with pytest.raises(ValidationError):
        LearnerPreferences.model_validate({"review_intensity": "extreme"})


def test_progress_schema_contracts() -> None:
    request = ProgressReportRequest.model_validate({"format": "markdown", "window_size": 1})
    assert request.format == "markdown"
    report = ProgressReport.model_validate(
        {
            "generated_at": "2026-05-21T12:00:00Z",
            "report_window": {
                "requested_session_count": 1,
                "actual_session_count": 0,
                "mastery_session_count": 0,
            },
            "snapshot": {
                "streak_days": 0,
                "due_count": 0,
                "maturity": {},
                "top_weak_patterns": [],
                "cost_status": "unavailable",
                "next_action": "Start vocabulary or writing practice.",
            },
            "recent_recap": {"actual_session_count": 0},
            "due_review_summary": {
                "due_count": 0,
                "completed_in_window": 0,
                "low_quality_in_window": 0,
                "maturity": {},
            },
        }
    )
    assert report.schema_version == 1
    assert report.cost_status == "unavailable"
    export = ProgressMarkdownExport(
        generated_at=report.generated_at,
        report_window=report.report_window,
        markdown="# Progress Report\n",
    )
    assert export.content_type == "text/markdown"
    trend = TextTrend(
        metric="answers",
        label="Answers",
        polarity="higher_is_better",
        direction="steady",
        sparkline="+++",
        min_label="min 1",
        max_label="max 1",
        values_count=3,
    )
    assert trend.sparkline == "+++"


# ---------------------------------------------------------------------------
# Host adapter setup contracts (spec 006)
# ---------------------------------------------------------------------------


def test_host_setup_target_rejects_unapproved_source() -> None:
    from language_tutor.schemas import HostId, HostSetupTarget, SetupModel

    with pytest.raises(ValidationError):
        HostSetupTarget(
            id=HostId.CLAUDE,
            display_name="Claude",
            official_source_url="https://example.com/not-approved",
            setup_model=SetupModel.PLUGIN_PACKAGE,
            primary_subagent="claude-subagent",
            contract_path="specs/006-agent-adapter-setup/contracts/host-setup-profiles/claude.md",
        )


def test_host_setup_target_rejects_wrong_contract_path() -> None:
    from language_tutor.schemas import APPROVED_HOST_SOURCES, HostId, HostSetupTarget, SetupModel

    with pytest.raises(ValidationError):
        HostSetupTarget(
            id=HostId.CLAUDE,
            display_name="Claude",
            official_source_url=APPROVED_HOST_SOURCES[HostId.CLAUDE.value],
            setup_model=SetupModel.PLUGIN_PACKAGE,
            primary_subagent="claude-subagent",
            contract_path="wrong/path.md",
        )


def test_host_id_accepts_only_four_targets() -> None:
    from language_tutor.schemas import HostId

    assert {h.value for h in HostId} == {"hermes", "openclaw", "claude", "codex"}
    with pytest.raises(ValueError):
        HostId("antigravity")


def test_official_source_evidence_requires_sections_and_facts() -> None:
    from language_tutor.schemas import OfficialSourceEvidence

    with pytest.raises(ValidationError):
        OfficialSourceEvidence(
            source_url="https://docs.claude.com",
            retrieved_on="2026-05-22",
            source_sections=[],
            facts_used=["install via plugin dir"],
        )


def test_host_setup_failure_is_non_empty_and_data_safe() -> None:
    from language_tutor.schemas import FailureCategory, FailurePhase, HostId, HostSetupFailure

    failure = HostSetupFailure(
        host=HostId.HERMES,
        phase=FailurePhase.INSTALL,
        category=FailureCategory.MISSING_PREREQUISITE,
        message="Hermes CLI not found on PATH.",
        remediation="Install the hermes CLI, then retry.",
        data_safety="No learner data modified.",
    )
    assert failure.host == HostId.HERMES.value
    with pytest.raises(ValidationError):
        HostSetupFailure(
            host=HostId.HERMES,
            phase=FailurePhase.INSTALL,
            category=FailureCategory.UNKNOWN,
            message="   ",
            remediation="x",
            data_safety="y",
        )


def test_host_json_schema_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    for name in (
        "host_capability_profile.schema.json",
        "host_setup_profile.schema.json",
        "lifecycle_trigger.schema.json",
        "conformance_run.schema.json",
        "manual_provider_install_report.schema.json",
    ):
        assert (tmp_path / name).exists()
        json.loads((tmp_path / name).read_text(encoding="utf-8"))
