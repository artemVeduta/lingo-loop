from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import click
from pydantic import BaseModel, ValidationError

from language_tutor.boot_context import build_boot_context, render_boot_context
from language_tutor.dal.paths import resolve_paths
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError, fail_json
from language_tutor.feedback import render_feedback
from language_tutor.health import doctor
from language_tutor.lessons import record_lesson, start_lesson
from language_tutor.lifecycle import end_session
from language_tutor.progress import progress_report
from language_tutor.progress_rendering import render_progress_markdown
from language_tutor.reading import record_reading, start_reading
from language_tutor.schemas import (
    BootContext,
    FeedbackEnvelope,
    LearnerPreferences,
    LearnerProfile,
    ProgressReport,
    ProgressReportRequest,
    SeedImportRequest,
    SessionEndInput,
    TextModalityRecordInput,
    VocabularyAnswerInput,
    VocabularyCardDefinition,
    VocabularyDrillRequest,
    VocabularyReviewHistoryRequest,
    WritingRecordInput,
)
from language_tutor.setup import read_setup, write_setup
from language_tutor.vocab import (
    add_vocab_card,
    answer_vocab,
    import_seed_list,
    review_history,
    start_vocab,
)
from language_tutor.writing import record_writing, writing_prompt


def emit(value: BaseModel | dict[str, Any]) -> None:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    click.echo(json.dumps(data, ensure_ascii=False, sort_keys=True))


def parse_payload(payload: str | None) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise TutorError(
            "invalid_json", "Payload is not valid JSON.", "Pass a JSON object string after --json."
        ) from exc
    if not isinstance(data, dict):
        raise TutorError("invalid_json", "Payload must be a JSON object.", "Pass a JSON object.")
    return cast(dict[str, Any], data)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def open_repo() -> tuple[TutorRepository, Any]:
    paths = resolve_paths()
    conn = connect(paths.database_path)
    return TutorRepository(conn), conn


@click.group()
def main() -> None:
    """Local-first language tutor."""


@main.command("doctor")
@click.option("--json-output", "--json", "json_output", is_flag=True, required=False)
def doctor_cmd(json_output: bool) -> None:
    del json_output
    try:
        emit(doctor(resolve_paths(), repo_root()))
    except TutorError as exc:
        fail_json(exc)


@main.group()
def setup() -> None:
    """Read or write setup."""


@setup.command("read")
@click.option("--json-output", "--json", "json_output", is_flag=True)
def setup_read(json_output: bool) -> None:
    del json_output
    try:
        emit(read_setup(resolve_paths()))
    except TutorError as exc:
        fail_json(exc)


@setup.command("write")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=False)
def setup_write(json_output: bool, payload: str | None) -> None:
    del json_output
    try:
        data = parse_payload(payload)
        profile = LearnerProfile.model_validate(data.get("profile", data))
        preferences_data = data.get("preferences")
        preferences = (
            LearnerPreferences.model_validate(preferences_data)
            if preferences_data is not None
            else None
        )
        emit(write_setup(resolve_paths(), profile, preferences))
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_setup",
                "Setup payload failed validation.",
                "Provide native_language and target_language.",
            )
        )


@main.command("boot-context")
@click.option("--json-output", "--json", "json_output", is_flag=True)
def boot_context_cmd(json_output: bool) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        repo, conn = open_repo()
        try:
            emit(build_boot_context(repo, state.profile, state.preferences))
        finally:
            conn.close()
    except TutorError as exc:
        fail_json(exc)


@main.group()
def render() -> None:
    """Render validated payloads."""


@render.command("boot-context")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def render_boot(json_output: bool, payload: str) -> None:
    del json_output
    try:
        context = BootContext.model_validate(parse_payload(payload))
        emit({"markdown": render_boot_context(context)})
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_boot_context",
                "Boot context failed validation.",
                "Pass tutor boot-context --json output.",
            )
        )


@render.command("feedback")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def render_feedback_cmd(json_output: bool, payload: str) -> None:
    del json_output
    try:
        feedback = FeedbackEnvelope.model_validate(parse_payload(payload))
        emit(
            {
                "markdown": render_feedback(feedback),
                "ascii_markdown": render_feedback(feedback, ascii_fallback=True),
            }
        )
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_feedback",
                "Feedback failed validation.",
                "Pass a FeedbackEnvelope JSON object.",
            )
        )


@render.command("progress-report")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def render_progress_report_cmd(json_output: bool, payload: str) -> None:
    del json_output
    try:
        report = ProgressReport.model_validate(parse_payload(payload))
        emit(render_progress_markdown(report))
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_progress_report",
                "Progress report failed validation.",
                "Pass tutor progress --json output.",
            )
        )


@main.group()
def vocab() -> None:
    """Vocabulary practice."""


@vocab.command("start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=False)
def vocab_start(json_output: bool, payload: str | None) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        request = VocabularyDrillRequest.model_validate(parse_payload(payload)) if payload else None
        repo, conn = open_repo()
        try:
            emit(start_vocab(repo, state.profile.target_language, state.preferences, request))
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_vocab_start",
                "Vocabulary start payload failed validation.",
                "Pass tags as a non-empty list or omit the payload.",
            )
        )


@vocab.command("add")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def vocab_add(json_output: bool, payload: str) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        definition = VocabularyCardDefinition.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(add_vocab_card(repo, definition, state.profile.target_language))
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_vocab_card",
                "Vocabulary card failed validation.",
                "Provide target, prompt, and accepted_answers; cloze prompts need one {{answer}} marker.",
            )
        )


@vocab.command("import")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def vocab_import(json_output: bool, payload: str) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        request = SeedImportRequest.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(import_seed_list(repo, request, state.profile.target_language))
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_seed_import",
                "Seed import payload failed validation.",
                "Pass {'path':'...json'} as the payload.",
            )
        )


@vocab.command("answer")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def vocab_answer(json_output: bool, payload: str) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        answer = VocabularyAnswerInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(answer_vocab(repo, answer, state.preferences))
        finally:
            conn.close()
    except (TutorError, ValidationError, KeyError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "vocab_answer_failed",
                "Vocabulary answer failed.",
                "Run vocab start and pass a valid item_id.",
            )
        )


@vocab.command("history")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def vocab_history(json_output: bool, payload: str) -> None:
    del json_output
    try:
        request = VocabularyReviewHistoryRequest.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(review_history(repo, request))
        finally:
            conn.close()
    except (TutorError, ValidationError, KeyError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        if isinstance(exc, KeyError):
            fail_json(
                TutorError(
                    "vocab_card_not_found",
                    "Vocabulary card was not found.",
                    "Run vocab start or import/add the card before requesting history.",
                )
            )
        fail_json(
            TutorError(
                "invalid_vocab_history",
                "Vocabulary history payload failed validation.",
                "Pass {'item_id':'...'} as the payload.",
            )
        )


@main.group()
def writing() -> None:
    """Free writing."""


@writing.command("prompt")
@click.option("--json-output", "--json", "json_output", is_flag=True)
def writing_prompt_cmd(json_output: bool) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        emit(writing_prompt(state.profile))
    except TutorError as exc:
        fail_json(exc)


@writing.command("record")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def writing_record_cmd(json_output: bool, payload: str) -> None:
    del json_output
    try:
        data = WritingRecordInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(record_writing(repo, data))
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "writing_record_failed",
                "Writing record failed validation.",
                "Pass WritingRecordInput JSON.",
            )
        )


@main.command("progress")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=False)
def progress_cmd(json_output: bool, payload: str | None) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        request = ProgressReportRequest.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            report = progress_report(repo, state.preferences, request)
            if request.format == "markdown":
                emit(render_progress_markdown(report))
            else:
                emit(report)
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_progress_request",
                "Progress request failed validation.",
                "Pass a JSON object with window_size 1-30 and optional generated_at.",
            )
        )


@main.command("session-end")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=False)
def session_end_cmd(json_output: bool, payload: str | None) -> None:
    del json_output
    try:
        data = SessionEndInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(end_session(repo, data))
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "session_end_failed",
                "Session-end payload failed validation.",
                "Pass SessionEndInput JSON.",
            )
        )


def _emit_text_modality_start(
    payload: str | None,
    start_fn: Any,
    invalid_code: str,
) -> None:
    try:
        state = read_setup(resolve_paths())
        emit(start_fn(parse_payload(payload), state.profile))
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                invalid_code,
                "Generated exercise candidate failed validation.",
                "Regenerate the candidate with required fields and a valid modality.",
            )
        )


def _emit_text_modality_record(payload: str, record_fn: Any) -> None:
    try:
        data = TextModalityRecordInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            emit(record_fn(repo, data))
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_text_modality_record",
                "Text-modality record payload failed validation.",
                "Pass TextModalityRecordInput JSON with a valid candidate_feedback.",
            )
        )


@main.group()
def reading() -> None:
    """Reading comprehension and transcript drills (text-only)."""


@reading.command("start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def reading_start(json_output: bool, payload: str) -> None:
    del json_output
    _emit_text_modality_start(payload, start_reading, "invalid_text_exercise")


@reading.command("record")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def reading_record(json_output: bool, payload: str) -> None:
    del json_output
    _emit_text_modality_record(payload, record_reading)


@main.group()
def lesson() -> None:
    """Guided micro-lessons (text-only)."""


@lesson.command("start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def lesson_start(json_output: bool, payload: str) -> None:
    del json_output
    _emit_text_modality_start(payload, start_lesson, "invalid_text_exercise")


@lesson.command("record")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def lesson_record(json_output: bool, payload: str) -> None:
    del json_output
    _emit_text_modality_record(payload, record_lesson)


if __name__ == "__main__":
    main()
