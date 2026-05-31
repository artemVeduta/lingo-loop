from __future__ import annotations

import json
from datetime import UTC, datetime
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
from language_tutor.lifecycle import end_session, start_session
from language_tutor.progress import progress_report
from language_tutor.progress_rendering import render_progress_markdown
from language_tutor.reading import record_reading, start_reading
from language_tutor.schemas import (
    BootContext,
    CheckpointModality,
    CheckpointStepKind,
    FeedbackEnvelope,
    HostId,
    LearnerPreferences,
    LearnerProfile,
    ProgressReport,
    ProgressReportRequest,
    ProviderState,
    ProviderStatus,
    SafeStepState,
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


def _read_menu_key() -> str:
    key = click.getchar()
    if key in ("\n", "\r"):
        return "enter"
    if key == " ":
        return "toggle"
    if key in ("\x1b[A", "\x00H"):
        return "up"
    if key in ("\x1b[B", "\x00P"):
        return "down"
    if key in ("\x1b[C", "\x00M"):
        return "right"
    if key in ("\x1b[D", "\x00K"):
        return "left"
    if key == "\x1b":
        try:
            second = click.getchar()
            if second == "[":
                third = click.getchar()
                return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(
                    third, "escape"
                )
        except EOFError:
            return "escape"
        return "escape"
    if key == "\x03":
        raise KeyboardInterrupt
    return "other"


def _is_selectable_provider(status: ProviderStatus) -> bool:
    return status.state not in {ProviderState.BLOCKED, ProviderState.UNKNOWN}


def _provider_state_text(status: ProviderStatus) -> str:
    return str(status.state)


def _selectable_cursor(statuses: list[ProviderStatus], start: int, step: int) -> int:
    if not statuses:
        return 0
    index = start
    for _ in statuses:
        index = (index + step) % len(statuses)
        if _is_selectable_provider(statuses[index]):
            return index
    return start


def _clear_terminal_screen() -> None:
    click.echo("\x1b[2J\x1b[H", nl=False)


def _render_detected_providers(statuses: list[ProviderStatus]) -> None:
    click.echo("Lingo Loop setup")
    click.echo("\nDetected providers")
    for status in statuses:
        marker = "x" if status.state == ProviderState.INSTALLED else " "
        click.echo(f"  [{marker}] {status.display_name:<14} {_provider_state_text(status):<12}")


def _render_provider_menu(
    statuses: list[ProviderStatus],
    selected: set[HostId],
    cursor: int,
    *,
    replace_previous: bool = False,
) -> None:
    if replace_previous:
        _clear_terminal_screen()
        _render_detected_providers(statuses)
    click.echo("\nInstall providers")
    click.echo("  Arrow keys move, Space toggles, Enter continues.")
    for idx, status in enumerate(statuses):
        selectable = _is_selectable_provider(status)
        pointer = ">" if idx == cursor and selectable else " "
        checkbox = "x" if status.host in selected else " "
        click.echo(
            f"  {pointer} [{checkbox}] {status.display_name:<14} {_provider_state_text(status):<12}"
        )


def _choose_providers(statuses: list[ProviderStatus]) -> list[HostId]:
    selectable = [s for s in statuses if _is_selectable_provider(s)]
    if not selectable:
        raise TutorError(
            "no_providers_available",
            "No supported host CLIs detected on PATH.",
            "Install at least one of: claude, codex, hermes, openclaw, then rerun.",
        )

    cursor = next(i for i, s in enumerate(statuses) if _is_selectable_provider(s))
    selected = {
        s.host
        for s in statuses
        if s.state in {ProviderState.INSTALLED, ProviderState.NEEDS_REPAIR}
    }
    if not selected:
        selected.add(statuses[cursor].host)

    _render_detected_providers(statuses)

    replace_previous_render = False
    while True:
        _render_provider_menu(statuses, selected, cursor, replace_previous=replace_previous_render)
        replace_previous_render = True
        key = _read_menu_key()
        if key == "up":
            cursor = _selectable_cursor(statuses, cursor, -1)
        elif key == "down":
            cursor = _selectable_cursor(statuses, cursor, 1)
        elif key == "toggle":
            host = statuses[cursor].host
            if host in selected:
                selected.remove(host)
            else:
                selected.add(host)
        elif key == "enter":
            if selected:
                return [s.host for s in statuses if s.host in selected]
            click.echo("Select at least one provider.")
        elif key == "escape":
            raise TutorError("init_aborted", "Provider selection aborted.", "Rerun tutor init.")


def _confirm_plan_apply() -> bool:
    selected = False
    while True:
        click.echo("\nApply install plan?")
        click.echo(f"  {'>' if not selected else ' '} No")
        click.echo(f"  {'>' if selected else ' '} Apply")
        click.echo("  Arrow keys move, Enter chooses.")
        key = _read_menu_key()
        if key in {"up", "down", "left", "right", "toggle"}:
            selected = not selected
        elif key == "enter":
            return selected
        elif key == "escape":
            return False


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
        if isinstance(exc, ValidationError):
            fields = ", ".join(
                ".".join(str(part) for part in error["loc"]) for error in exc.errors()
            )
            fail_json(
                TutorError(
                    "vocab_answer_failed",
                    "Vocabulary answer payload failed validation.",
                    f"Fix these payload fields: {fields}.",
                )
            )
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


@main.command("session-close")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def session_close_cmd(json_output: bool, payload: str) -> None:
    """Manually close a session: mark ``status=closed``, set ``closed_at``,
    flush summary + costs + next focus. Never called automatically (FR-007)."""
    del json_output
    try:
        data = parse_payload(payload)
        sid = data.get("session_id")
        if not isinstance(sid, str) or not sid:
            raise TutorError(
                "invalid_session_close",
                "session_id is required.",
                "Pass the session_id returned by session-start.",
            )
        end_input = SessionEndInput.model_validate(data)
        repo, conn = open_repo()
        try:
            try:
                repo.close_session(sid, now=_utc_now())
            except KeyError as exc:
                raise TutorError(
                    "session_not_closable",
                    f"Session {sid} is not open (missing or already closed).",
                    "Call session-close on an open session_id.",
                ) from exc
            result = end_session(repo, end_input)
        finally:
            conn.close()
        emit(result)
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_session_close",
                "Session-close payload failed validation.",
                "Pass session_id, analysis, costs.",
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


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


@main.command("session-start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def session_start_cmd(json_output: bool, payload: str) -> None:
    """Mint a tutor session id and return boot context + prior-session history.

    PAYLOAD is a JSON object. "host" is required; "host_conversation_id" is
    optional. Example:

        tutor session-start --json '{"host":"claude|codex|openclaw|hermes"}'
    """
    del json_output
    try:
        data = parse_payload(payload)
        host_value = data.get("host")
        if not isinstance(host_value, str):
            raise TutorError(
                "invalid_session_start",
                "host is required.",
                'Pass {"host":"claude|codex|openclaw|hermes"}.',
            )
        try:
            host = HostId(host_value)
        except ValueError as exc:
            raise TutorError(
                "unsupported_host",
                f"Host '{host_value}' is not supported.",
                "Use one of: hermes, openclaw, claude, codex.",
            ) from exc
        host_conversation_id = data.get("host_conversation_id")
        if host_conversation_id is not None and not isinstance(host_conversation_id, str):
            raise TutorError(
                "invalid_session_start",
                "host_conversation_id must be a string when provided.",
                "Omit it or pass a string.",
            )
        state = read_setup(resolve_paths())
        repo, conn = open_repo()
        try:
            result = start_session(
                repo,
                profile=state.profile,
                preferences=state.preferences,
                host=host,
                host_conversation_id=host_conversation_id,
                now=_utc_now(),
            )
        finally:
            conn.close()
        emit(result)
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_session_start",
                "Session-start payload failed validation.",
                'Pass {"host":"claude|codex|openclaw|hermes"} (host required).',
            )
        )


@main.command("checkpoint")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def checkpoint_cmd(json_output: bool, payload: str) -> None:
    """Record a durable per-step checkpoint under the active session."""
    del json_output
    try:
        data = parse_payload(payload)
        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise TutorError(
                "invalid_checkpoint",
                "session_id is required.",
                "Pass the session_id returned by session-start.",
            )
        modality_value = data.get("modality")
        step_kind_value = data.get("step_kind")
        if not isinstance(modality_value, str) or not isinstance(step_kind_value, str):
            raise TutorError(
                "invalid_checkpoint",
                "modality and step_kind are required.",
                "Pass modality and step_kind as strings.",
            )
        try:
            modality = CheckpointModality(modality_value)
            step_kind = CheckpointStepKind(step_kind_value)
        except ValueError as exc:
            raise TutorError(
                "invalid_checkpoint",
                "modality or step_kind is not a known value.",
                "Use a documented modality and step_kind.",
            ) from exc
        prompt_ref_value = data.get("prompt_ref")
        prompt_ref = prompt_ref_value if isinstance(prompt_ref_value, str) else None
        state_payload: dict[str, Any] = {}
        raw_state = data.get("state")
        if raw_state is not None:
            if not isinstance(raw_state, dict):
                raise TutorError(
                    "invalid_checkpoint",
                    "state must be an object.",
                    "Pass safe step metadata only (prompt_ref, step_index, total_steps, labels).",
                )
            state_payload = cast(dict[str, Any], raw_state)
        state = SafeStepState.model_validate(state_payload)
        summary = data.get("summary", "")
        if not isinstance(summary, str):
            raise TutorError(
                "invalid_checkpoint",
                "summary must be a string.",
                "Pass a short rolling summary string.",
            )
        repo, conn = open_repo()
        try:
            try:
                checkpoint = repo.record_checkpoint(
                    session_id=session_id,
                    modality=modality,
                    step_kind=step_kind,
                    prompt_ref=prompt_ref,
                    state=state,
                    summary=summary,
                    now=_utc_now(),
                )
            except KeyError as exc:
                raise TutorError(
                    "session_not_found",
                    f"Session {session_id} does not exist.",
                    "Call session-start first and thread its session_id.",
                ) from exc
        finally:
            conn.close()
        emit(checkpoint)
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_checkpoint",
                "Checkpoint payload failed validation.",
                "Pass session_id, modality, step_kind, state, summary.",
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
        fields = ", ".join(
            ".".join(str(part) for part in error["loc"]) for error in exc.errors()
        )
        fail_json(
            TutorError(
                invalid_code,
                "Generated exercise candidate failed validation.",
                f"Regenerate the candidate; fix these fields: {fields}.",
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


@main.group()
def host() -> None:
    """Host adapter capability, boot trigger, profile, and conformance checks."""


@host.command("targets")
@click.option("--json-output", "--json", "json_output", is_flag=True)
def host_targets(json_output: bool) -> None:
    """List the supported host setup targets."""
    del json_output
    from language_tutor.adapters.base import supported_host_targets

    targets = supported_host_targets()
    emit({"targets": [t.model_dump(mode="json") for t in targets.values()]})


@host.command("capability")
@click.argument("host_id", required=True)
@click.option("--json-output", "--json", "json_output", is_flag=True)
def host_capability(host_id: str, json_output: bool) -> None:
    """Emit the declared capability profile for a host."""
    del json_output
    from language_tutor.adapters.base import is_supported_host
    from language_tutor.adapters.registry import capability_profile_for

    if not is_supported_host(host_id):
        fail_json(
            TutorError(
                "unsupported_host",
                f"Host '{host_id}' is not a supported setup target.",
                "Use one of: hermes, openclaw, claude, codex.",
            )
        )
    emit(capability_profile_for(host_id))


@host.command("boot-trigger")
@click.argument("host_id", required=True)
@click.option("--json-output", "--json", "json_output", is_flag=True)
def host_boot_trigger(host_id: str, json_output: bool) -> None:
    """Emit the deterministic boot trigger selected for a host."""
    del json_output
    from language_tutor.adapters.base import is_supported_host
    from language_tutor.adapters.registry import capability_profile_for
    from language_tutor.boot_context import select_boot_trigger

    if not is_supported_host(host_id):
        fail_json(
            TutorError(
                "unsupported_host",
                f"Host '{host_id}' is not a supported setup target.",
                "Use one of: hermes, openclaw, claude, codex.",
            )
        )
    profile = capability_profile_for(host_id)
    emit(select_boot_trigger(profile.boot_context_trigger))


@main.command("init")
@click.option(
    "--provider",
    "providers",
    multiple=True,
    type=click.Choice([h.value for h in HostId], case_sensitive=False),
    help="Provider id to install (repeat for multiple). Omit for interactive selection.",
)
@click.option("--yes", is_flag=True, help="Skip confirmation prompts (required when non-TTY).")
@click.option("--dry-run", is_flag=True, help="Plan only; do not write any files.")
@click.option("--json-output", "--json", "json_output", is_flag=True, help="Emit InitResult JSON.")
def init_cmd(
    providers: tuple[str, ...], yes: bool, dry_run: bool, json_output: bool
) -> None:
    """Detect supported AI hosts and install/repair selected provider wiring."""
    from language_tutor.installer import InstallerContext
    from language_tutor.installer.assets import bundled_assets_root
    from language_tutor.installer.registry import SUPPORTED_PROVIDER_IDS, build_installer
    from language_tutor.installer.seams import is_tty
    from language_tutor.installer.service import build_plan, run_init
    from language_tutor.schemas import InitRequest, ProviderActionStage

    try:
        ctx = InstallerContext.real(bundled_assets_root())
        selected_ids = [HostId(p) for p in providers]
        non_interactive = not is_tty() or yes or providers or json_output
        if json_output and not dry_run and not yes:
            raise TutorError(
                "init_json_write_requires_yes",
                "tutor init refuses to write from --json mode without --yes.",
                "Pass --yes for writes, or add --dry-run to inspect the plan.",
            )
        if not is_tty() and not (providers and yes) and not dry_run:
            raise TutorError(
                "init_non_interactive_unsafe",
                "tutor init refuses to run non-interactively without --provider and --yes.",
                "Pass --provider <id> (repeatable) plus --yes, or run in an interactive terminal.",
            )

        if not selected_ids and not non_interactive:
            statuses: list[ProviderStatus] = []
            for host in SUPPORTED_PROVIDER_IDS:
                installer = build_installer(host, ctx)
                statuses.append(installer.detect())
            selected_ids = _choose_providers(statuses)

        if not selected_ids:
            selected_ids = list(SUPPORTED_PROVIDER_IDS)

        request = InitRequest(
            providers=selected_ids,
            yes=yes,
            dry_run=dry_run,
            json_output=json_output,
        )

        if not json_output:
            plan = build_plan(ctx, request)
            click.echo("\nPlan:")
            for pp in plan.plans:
                click.echo(f"  {pp.status.display_name} [{pp.status.state}]")
                for action in pp.actions:
                    click.echo(f"    - {action.kind}: {action.description}")
            if not dry_run and not yes and not _confirm_plan_apply():
                click.echo("Aborted.")
                return

        result = run_init(ctx, request)

        if json_output:
            emit(result)
            return

        click.echo("\nResult:")
        for r in result.results:
            verified = "verified" if r.verified else str(r.status.state)
            click.echo(f"  {r.status.display_name:<14} {verified}")
            for action in r.actions:
                stage = str(action.stage)
                marker = "✓" if action.stage == ProviderActionStage.APPLIED else "-"
                click.echo(f"    {marker} {stage}: {action.target_path}")
            if r.next_command:
                click.echo(f"    next: {r.next_command}")
            if r.repair_hint:
                click.echo(f"    hint: {r.repair_hint}")
    except TutorError as exc:
        fail_json(exc)


if __name__ == "__main__":
    main()
