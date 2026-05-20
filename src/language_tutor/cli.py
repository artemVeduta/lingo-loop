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
from language_tutor.lifecycle import end_session
from language_tutor.progress import progress_report
from language_tutor.schemas import (
    BootContext,
    FeedbackEnvelope,
    LearnerPreferences,
    LearnerProfile,
    SessionEndInput,
    VocabularyAnswerInput,
    WritingRecordInput,
)
from language_tutor.setup import read_setup, write_setup
from language_tutor.vocab import answer_vocab, start_vocab
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


@main.group()
def vocab() -> None:
    """Vocabulary practice."""


@vocab.command("start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
def vocab_start(json_output: bool) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        repo, conn = open_repo()
        try:
            emit(start_vocab(repo, state.profile.target_language, state.preferences))
            conn.commit()
        finally:
            conn.close()
    except TutorError as exc:
        fail_json(exc)


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
def progress_cmd(json_output: bool) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        repo, conn = open_repo()
        try:
            emit(progress_report(repo, state.preferences))
        finally:
            conn.close()
    except TutorError as exc:
        fail_json(exc)


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


if __name__ == "__main__":
    main()
