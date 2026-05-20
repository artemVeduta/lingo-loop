from __future__ import annotations

import re
from collections.abc import Iterable

from language_tutor.schemas import (
    Confidence,
    ErrorSpan,
    ErrorTag,
    FeedbackEnvelope,
    Severity,
    Verdict,
)

CYRILLIC_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "h",
        "ґ": "g",
        "д": "d",
        "е": "e",
        "є": "ie",
        "ж": "zh",
        "з": "z",
        "и": "y",
        "і": "i",
        "ї": "i",
        "й": "i",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ю": "iu",
        "я": "ia",
        "ь": "",
        "'": "",
    }
)


def normalize_answer(value: str, transliteration_tolerance: bool = False) -> str:
    clean = re.sub(r"\s+", " ", value.strip().lower())
    clean = re.sub(r"[.!?,;:]+$", "", clean)
    if transliteration_tolerance:
        clean = clean.translate(CYRILLIC_LATIN)
    return clean


def compare_answer(
    answer: str, accepted_answers: Iterable[str], transliteration_tolerance: bool = False
) -> Verdict:
    normalized = normalize_answer(answer, transliteration_tolerance)
    if normalized in {"", "i don't know", "idk", "не знаю"}:
        return Verdict.UNANSWERED
    accepted = {
        normalize_answer(candidate, transliteration_tolerance) for candidate in accepted_answers
    }
    if normalized in accepted:
        return Verdict.CORRECT
    if any(
        normalized and (normalized in candidate or candidate in normalized)
        for candidate in accepted
    ):
        return Verdict.PARTIAL
    return Verdict.MISSED


def vocabulary_feedback(
    answer: str, accepted_answers: list[str], transliteration_tolerance: bool = False
) -> FeedbackEnvelope:
    verdict = compare_answer(answer, accepted_answers, transliteration_tolerance)
    if verdict == Verdict.CORRECT:
        return FeedbackEnvelope(
            verdict=verdict,
            corrected_answer=accepted_answers[0],
            severity=Severity.NONE,
            confidence=Confidence.HIGH,
            explanation="Correct.",
            next_drill_hint="Review again when due.",
        )
    if verdict == Verdict.PARTIAL:
        return FeedbackEnvelope(
            verdict=verdict,
            corrected_answer=accepted_answers[0],
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            error_spans=[
                ErrorSpan(
                    text=answer,
                    tag=ErrorTag.SPELLING,
                    severity=Severity.LOW,
                    explanation="Close answer; adjust the form.",
                )
            ],
            explanation="Close. Use the accepted form.",
            next_drill_hint="Repeat the full target form once.",
        )
    if verdict == Verdict.UNANSWERED:
        return FeedbackEnvelope(
            verdict=verdict,
            corrected_answer=accepted_answers[0],
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            explanation="No answer recorded.",
            next_drill_hint="Say the answer aloud before viewing it.",
        )
    return FeedbackEnvelope(
        verdict=verdict,
        corrected_answer=accepted_answers[0],
        severity=Severity.MEDIUM,
        confidence=Confidence.HIGH,
        error_spans=[
            ErrorSpan(
                text=answer,
                tag=ErrorTag.VOCABULARY,
                severity=Severity.MEDIUM,
                explanation="Use the expected vocabulary item.",
            )
        ],
        explanation="Use the target answer.",
        next_drill_hint="Practice the prompt-answer pair.",
    )


def sanitize_feedback(feedback: FeedbackEnvelope) -> FeedbackEnvelope:
    spans: list[ErrorSpan] = []
    for span in feedback.error_spans:
        if feedback.confidence == Confidence.LOW and span.severity == Severity.HIGH:
            spans.append(span.model_copy(update={"severity": Severity.MEDIUM}))
        else:
            spans.append(span)
    if not feedback.next_drill_hint:
        feedback = feedback.model_copy(update={"next_drill_hint": "Practice one similar sentence."})
    return feedback.model_copy(update={"error_spans": spans})


def render_feedback(feedback: FeedbackEnvelope, *, ascii_fallback: bool = False) -> str:
    marker = "[!]" if ascii_fallback else "•"
    lines = [
        f"{marker} Verdict: {feedback.verdict}",
        f"{marker} Severity: {feedback.severity}",
        f"{marker} Correction: {feedback.corrected_answer or 'n/a'}",
        f"{marker} Explanation: {feedback.explanation or 'No explanation provided.'}",
    ]
    for span in feedback.error_spans:
        lines.append(f"{marker} {span.tag}: {span.text} - {span.explanation}")
    lines.append(f"{marker} Next drill: {feedback.next_drill_hint}")
    return "\n".join(lines)
