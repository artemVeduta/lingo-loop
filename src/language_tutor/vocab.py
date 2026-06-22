from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from language_tutor.errors import TutorError
from language_tutor.feedback import vocabulary_feedback
from language_tutor.schemas import (
    LearnerPreferences,
    SeedImportEntryResult,
    SeedImportRequest,
    SeedImportResult,
    SelectionPolicy,
    SelectionReason,
    VocabularyAnswerInput,
    VocabularyAnswerResult,
    VocabularyCardAddResult,
    VocabularyCardDefinition,
    VocabularyDrillRequest,
    VocabularyItem,
    VocabularyReviewHistory,
    VocabularyReviewHistoryRequest,
    VocabularySelectionSource,
    VocabularySessionPlan,
    WeakTagSignal,
    WeakTagSourceCounts,
    WeakTagSourceEvent,
)
from language_tutor.srs import quality_for_verdict, schedule_review

if TYPE_CHECKING:
    from language_tutor.dal.repositories import TutorRepository


APOSTROPHE_VARIANTS = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "＇": "'"})
CLOZE_MARKER = "{{answer}}"
SelectionReasonLabel = Literal[
    "overdue",
    "due",
    "weak_tag_match",
    "explicit_filter_match",
    "reserved_non_weak_due",
    "new_card_fill",
]


def queue_size(preferences: LearnerPreferences) -> int:
    multiplier = {"light": 0.5, "normal": 1.0, "heavy": 1.5}[str(preferences.review_intensity)]
    return min(60, max(1, round(preferences.session_length * multiplier)))


def requested_queue_size(preferences: LearnerPreferences) -> int:
    multiplier = {"light": 0.5, "normal": 1.0, "heavy": 1.5}[str(preferences.review_intensity)]
    return max(1, round(preferences.session_length * multiplier))


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).translate(APOSTROPHE_VARIANTS).casefold()
    text = re.sub(r"\s+", " ", text.strip())
    while text and unicodedata.category(text[0]).startswith("P"):
        text = text[1:].strip()
    while text and unicodedata.category(text[-1]).startswith("P"):
        text = text[:-1].strip()
    return text


def normalize_tag(value: str) -> str:
    return normalize_text(value)


def dedupe_key(card_type: str, target: str, prompt: str) -> str:
    return f"{card_type}:{normalize_text(target)}:{normalize_text(prompt)}"


def dedupe_key_for_item(item: VocabularyItem) -> str:
    return dedupe_key(item.card_type, item.lemma or item.prompt, item.prompt)


def merge_display_values(existing: list[str], incoming: list[str]) -> tuple[list[str], bool]:
    merged = list(existing)
    seen = {normalize_text(value) for value in existing}
    changed = False
    for value in incoming:
        key = normalize_text(value)
        if key and key not in seen:
            merged.append(value.strip())
            seen.add(key)
            changed = True
    return merged, changed


def merge_tags(existing: list[str], incoming: list[str]) -> tuple[list[str], bool]:
    merged = list(existing)
    seen = {normalize_tag(value) for value in existing}
    changed = False
    for value in incoming:
        key = normalize_tag(value)
        if key and key not in seen:
            merged.append(value.strip())
            seen.add(key)
            changed = True
    return merged, changed


def normalized_tag_filter(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        key = normalize_tag(tag)
        if key and key not in seen:
            normalized.append(key)
            seen.add(key)
    if not normalized:
        raise TutorError("invalid_vocab_filter", "Tag filter is empty.", "Pass at least one tag.")
    return normalized


def active_weak_tag_signals(
    events: list[WeakTagSourceEvent], *, limit: int = 5
) -> list[WeakTagSignal]:
    session_tags: dict[str, set[str]] = {}
    latest: dict[str, datetime] = {}
    source_counts: dict[str, WeakTagSourceCounts] = {}
    for event in events:
        tag = normalize_tag(event.tag)
        if not tag:
            continue
        session_tags.setdefault(tag, set()).add(event.session_id)
        latest[tag] = max(latest.get(tag, event.observed_at), event.observed_at)
        counts = source_counts.setdefault(tag, WeakTagSourceCounts())
        if event.source == "mistake_events":
            counts.mistake_events += 1
        else:
            counts.low_quality_reviews += 1

    active = [
        (tag, sessions)
        for tag, sessions in session_tags.items()
        if len(sessions) >= 2
    ]
    active.sort(key=lambda item: (-len(item[1]), -latest[item[0]].timestamp(), item[0]))
    return [
        WeakTagSignal(
            tag=tag,
            session_count=len(sessions),
            latest_seen_at=latest[tag],
            priority_rank=index,
            source_counts=source_counts[tag],
        )
        for index, (tag, sessions) in enumerate(active[:limit], start=1)
    ]


def derive_active_weak_tag_signals(
    repo: TutorRepository, *, recent_session_limit: int = 10, weak_tag_limit: int = 5
) -> list[WeakTagSignal]:
    session_ids = repo.recent_analyzed_session_ids(recent_session_limit)
    return active_weak_tag_signals(
        repo.weak_tag_source_events(session_ids),
        limit=weak_tag_limit,
    )


@dataclass(frozen=True)
class SelectionCandidate:
    source: VocabularySelectionSource
    normalized_tags: tuple[str, ...]
    is_new: bool
    is_due: bool
    is_overdue: bool
    matched_weak_tags: tuple[str, ...]
    matches_explicit_filter: bool

    @property
    def item(self) -> VocabularyItem:
        return self.source.item

    @property
    def due_at(self) -> datetime:
        return self.item.state.due_at

    @property
    def created_at(self) -> datetime:
        return self.source.created_at


def selection_candidates(
    sources: list[VocabularySelectionSource],
    *,
    now: datetime,
    active_weak_tags: list[WeakTagSignal],
    explicit_filter_active: bool,
) -> list[SelectionCandidate]:
    weak_order = {signal.tag: signal.priority_rank for signal in active_weak_tags}
    today = now.astimezone(UTC).date()
    candidates: list[SelectionCandidate] = []
    for source in sources:
        tags = tuple(dict.fromkeys(normalize_tag(tag) for tag in source.item.tags if normalize_tag(tag)))
        state = source.item.state
        due_at = state.due_at.astimezone(UTC)
        is_new = state.state == "new"
        is_due = not is_new and due_at <= now
        matched = tuple(sorted((tag for tag in tags if tag in weak_order), key=weak_order.__getitem__))
        candidates.append(
            SelectionCandidate(
                source=source,
                normalized_tags=tags,
                is_new=is_new,
                is_due=is_due,
                is_overdue=is_due and due_at.date() < today,
                matched_weak_tags=matched,
                matches_explicit_filter=explicit_filter_active,
            )
        )
    return candidates


def _due_tie_key(candidate: SelectionCandidate) -> tuple[datetime, datetime, str, str]:
    return (
        candidate.due_at,
        candidate.created_at,
        normalize_text(candidate.item.prompt),
        candidate.item.id,
    )


def _new_tie_key(candidate: SelectionCandidate) -> tuple[datetime, str, str]:
    return (candidate.created_at, normalize_text(candidate.item.prompt), candidate.item.id)


def _weak_rank(candidate: SelectionCandidate, weak_order: dict[str, int]) -> int:
    if not candidate.matched_weak_tags:
        return 1_000_000
    return min(weak_order[tag] for tag in candidate.matched_weak_tags)


def select_vocabulary_queue(
    candidates: list[SelectionCandidate],
    *,
    effective_count: int,
    active_weak_tags: list[WeakTagSignal],
) -> tuple[list[VocabularyItem], list[SelectionReason], bool]:
    weak_order = {signal.tag: signal.priority_rank for signal in active_weak_tags}
    overdue = sorted((c for c in candidates if c.is_overdue), key=_due_tie_key)
    due_today = sorted(
        (c for c in candidates if c.is_due and not c.is_overdue),
        key=lambda c: (_weak_rank(c, weak_order), *_due_tie_key(c)),
    )
    due_pool = overdue + due_today
    selected: list[SelectionCandidate] = due_pool[:effective_count]
    reserved = False
    due_capacity = min(effective_count, len(due_pool))
    if due_capacity >= 2 and all(candidate.matched_weak_tags for candidate in selected):
        non_weak_due = sorted((c for c in due_pool if not c.matched_weak_tags), key=_due_tie_key)
        if non_weak_due:
            replacement = non_weak_due[0]
            if replacement not in selected:
                selected = selected[: due_capacity - 1] + [replacement]
            reserved = True

    if len(selected) < effective_count:
        selected_ids = {candidate.item.id for candidate in selected}
        new_cards = sorted(
            (c for c in candidates if c.is_new and c.item.id not in selected_ids),
            key=lambda c: (_weak_rank(c, weak_order), *_new_tie_key(c)),
        )
        selected.extend(new_cards[: effective_count - len(selected)])

    reasons: list[SelectionReason] = []
    for rank, candidate in enumerate(selected, start=1):
        if candidate.is_overdue:
            bucket = "overdue_due"
            reason_labels: list[SelectionReasonLabel] = ["overdue"]
        elif candidate.is_due:
            bucket = "due_today"
            reason_labels = ["due"]
        else:
            bucket = "new_fill"
            reason_labels = ["new_card_fill"]
        if candidate.matches_explicit_filter:
            reason_labels.append("explicit_filter_match")
        if candidate.matched_weak_tags:
            reason_labels.append("weak_tag_match")
        if reserved and candidate.is_due and not candidate.matched_weak_tags:
            reason_labels.append("reserved_non_weak_due")
        reasons.append(
            SelectionReason(
                item_id=candidate.item.id,
                rank=rank,
                bucket=bucket,
                reasons=reason_labels,
                matched_weak_tags=list(candidate.matched_weak_tags),
                due_at=candidate.due_at if candidate.is_due else None,
            )
        )
    return [candidate.item for candidate in selected], reasons, reserved


def cloze_prompt(prompt: str) -> str:
    return prompt.replace(CLOZE_MARKER, "____")


def cloze_reveal(prompt: str, answer: str) -> str:
    return prompt.replace(CLOZE_MARKER, answer)


def presentation_item(item: VocabularyItem) -> VocabularyItem:
    if item.card_type != "cloze":
        return item
    return item.model_copy(update={"prompt": cloze_prompt(item.prompt)})


def item_from_definition(
    definition: VocabularyCardDefinition, target_language: str, item_id: str
) -> VocabularyItem:
    return VocabularyItem(
        id=item_id,
        card_type=definition.card_type,
        target_language=target_language,
        prompt=definition.prompt,
        lemma=definition.target,
        accepted_answers=definition.accepted_answers,
        hint=definition.hint,
        notes=definition.notes_list(),
        sources=definition.sources_list(),
        tags=definition.tags,
    )


def start_vocab(
    repo: TutorRepository,
    target_language: str,
    preferences: LearnerPreferences,
    request: VocabularyDrillRequest | None = None,
) -> VocabularySessionPlan:
    requested_count = (
        request.requested_count if request and request.requested_count else requested_queue_size(preferences)
    )
    effective_count = min(60, max(1, requested_count))
    now = datetime.now(UTC)
    filter_tags = normalized_tag_filter(request.tags) if request and request.tags is not None else []
    sources = repo.vocabulary_selection_candidates(filter_tags or None)
    if not sources and not filter_tags:
        repo.seed_default_vocabulary(target_language)
        sources = repo.vocabulary_selection_candidates(None)

    active_signals = derive_active_weak_tag_signals(repo)
    candidates = selection_candidates(
        sources,
        now=now,
        active_weak_tags=active_signals,
        explicit_filter_active=bool(filter_tags),
    )
    items, reasons, reserved_non_weak = select_vocabulary_queue(
        candidates,
        effective_count=effective_count,
        active_weak_tags=active_signals,
    )
    matching_count = len(sources) if filter_tags else None
    due_matching_count = sum(candidate.is_due for candidate in candidates) if filter_tags else None
    empty_reason = None
    if filter_tags and not items:
        empty_reason = "no_matching_cards" if matching_count == 0 else "matching_cards_not_due"
    return VocabularySessionPlan(
        items=[presentation_item(item) for item in items],
        requested_count=requested_count,
        effective_count=effective_count,
        starter_content_required=not bool(items),
        filter=filter_tags,
        matching_count=matching_count,
        due_matching_count=due_matching_count,
        empty_reason=empty_reason,
        active_weak_tags=active_signals,
        selection_reasons=reasons,
        selection_policy=SelectionPolicy(
            reserved_non_weak_due_slot=reserved_non_weak,
            intensity=preferences.review_intensity,
        ),
    )


def add_vocab_card(
    repo: TutorRepository,
    definition: VocabularyCardDefinition,
    target_language: str,
) -> VocabularyCardAddResult:
    item = item_from_definition(definition, target_language, repo.create_id("vocab"))
    existing_id = repo.find_vocabulary_duplicate(item)
    if existing_id is not None:
        return VocabularyCardAddResult(
            status="duplicate",
            item_id=existing_id,
            duplicate=True,
            message="Duplicate card rejected.",
            repair_hint="Use a different target, prompt, or card_type.",
        )
    item_id = repo.insert_vocabulary_item(item)
    return VocabularyCardAddResult(
        status="created", item_id=item_id, duplicate=False, message="Card created."
    )


def find_or_create_vocab_card_for_book(
    repo: TutorRepository,
    *,
    word: str,
    translation: str,
    gloss: str | None,
    book_source: str,
    target_language: str,
) -> tuple[Literal["created", "updated", "skipped"], str]:
    """Find-or-create the global SRS card for a book word lookup.

    Composes a VocabularyCardDefinition (card_type=standard, target=word -> lemma,
    prompt=word, accepted_answers=[translation], tags=["from-book"], source=book)
    and reuses item_from_definition + the nestable _import_vocabulary_item_inner
    so the card write merges into the caller's outer transaction. The card is
    deduped globally by standard:<word>:<word>.
    """
    definition = VocabularyCardDefinition(
        card_type="standard",
        target=word,
        prompt=word,
        accepted_answers=[translation],
        hint=gloss,
        notes=[gloss] if gloss else None,
        source=book_source,
        tags=["from-book"],
    )
    item = item_from_definition(definition, target_language, repo.create_id("vocab"))
    return repo._import_vocabulary_item_inner(item)


def import_seed_list(
    repo: TutorRepository,
    request: SeedImportRequest,
    target_language: str,
) -> SeedImportResult:
    path = Path(request.path)
    if path.suffix != ".json":
        raise TutorError("invalid_seed_path", "Seed path must be a .json file.", "Pass a JSON file.")
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TutorError(
            "seed_file_unreadable", "Seed file cannot be read.", "Check the path and permissions."
        ) from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TutorError(
            "invalid_seed_json", "Seed file is not valid JSON.", "Fix JSON syntax and retry."
        ) from exc
    if not isinstance(payload, list):
        raise TutorError("invalid_seed_json", "Seed JSON must be a list.", "Use a top-level list.")
    if not payload:
        raise TutorError("empty_seed_json", "Seed list is empty.", "Add at least one card object.")

    entries: list[SeedImportEntryResult] = []
    seed_entries = cast(list[object], payload)
    for index, raw_entry in enumerate(seed_entries):
        if not isinstance(raw_entry, dict):
            entries.append(
                SeedImportEntryResult(
                    index=index,
                    status="invalid",
                    code="invalid_seed_entry",
                    message="Seed entry must be an object.",
                    repair_hint="Use a JSON object for each card.",
                )
            )
            continue
        try:
            definition = VocabularyCardDefinition.model_validate(raw_entry)
            item = item_from_definition(definition, target_language, repo.create_id("vocab"))
            status, item_id = repo.import_vocabulary_item(item)
            entries.append(SeedImportEntryResult(index=index, status=status, item_id=item_id))
        except Exception as exc:  # noqa: BLE001
            entries.append(
                SeedImportEntryResult(
                    index=index,
                    status="invalid",
                    code="invalid_seed_entry",
                    message="Seed entry failed validation.",
                    repair_hint=str(exc),
                )
            )
    return SeedImportResult(
        path=str(path),
        created_count=sum(entry.status == "created" for entry in entries),
        updated_count=sum(entry.status == "updated" for entry in entries),
        skipped_count=sum(entry.status == "skipped" for entry in entries),
        invalid_count=sum(entry.status == "invalid" for entry in entries),
        entries=entries,
    )


def answer_vocab(
    repo: TutorRepository, payload: VocabularyAnswerInput, preferences: LearnerPreferences
) -> VocabularyAnswerResult:
    item = repo.get_vocabulary_item(payload.item_id)
    feedback = vocabulary_feedback(
        payload.answer, item.accepted_answers, preferences.transliteration_tolerance
    )
    if item.card_type == "cloze":
        reveal = cloze_reveal(item.prompt, item.lemma or item.accepted_answers[0])
        feedback = feedback.model_copy(
            update={
                "cloze_sentence": reveal,
                "accepted_answer": item.accepted_answers[0],
                "explanation": f"{feedback.explanation} Sentence: {reveal}",
            }
        )
    next_state = schedule_review(item.state, feedback.verdict)
    quality = quality_for_verdict(feedback.verdict)
    return repo.record_vocab_answer(
        item=item,
        session_id=payload.session_id,
        answer=payload.answer,
        idempotency_key=payload.idempotency_key,
        feedback=feedback,
        previous_state=item.state,
        next_state=next_state,
        quality=quality,
    )


def review_history(
    repo: TutorRepository, request: VocabularyReviewHistoryRequest
) -> VocabularyReviewHistory:
    return repo.vocabulary_review_history(request.item_id, datetime.now(UTC))
