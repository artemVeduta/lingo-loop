from __future__ import annotations

from typing import Any


def reading_candidate(**overrides: Any) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "modality": "reading",
        "target_language": "Ukrainian",
        "level_target": "A2",
        "focus": "case",
        "instructions": "Read the passage and answer the questions briefly.",
        "content": "Марія купила книгу в магазині. Потім вона пішла додому.",
        "questions": ["Що купила Марія?", "Куди вона пішла?"],
        "answer_key": ["книгу", "додому"],
        "rubric": ["Correct accusative object.", "Correct direction."],
        "tags": ["case"],
    }
    candidate.update(overrides)
    return candidate


def lesson_candidate(**overrides: Any) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "modality": "lesson",
        "target_language": "Ukrainian",
        "level_target": "A2",
        "focus": "verbs_of_motion",
        "instructions": "Read the explanation, then complete the practice step.",
        "content": "Ukrainian uses йти for going on foot and їхати for going by vehicle.",
        "questions": ["Complete: Я ___ до школи пішки."],
        "answer_key": ["йду"],
        "rubric": ["Uses the on-foot verb of motion."],
        "tags": ["verbs_of_motion"],
    }
    candidate.update(overrides)
    return candidate


def transcript_candidate(**overrides: Any) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "modality": "transcript",
        "mode": "transcript_reconstruction",
        "target_language": "Ukrainian",
        "level_target": "A2",
        "focus": "word_order",
        "instructions": "Reconstruct the text-only transcript in correct word order.",
        "content": "магазині / купила / Марія / у / книгу",
        "questions": ["Reorder the words into a correct sentence."],
        "answer_key": ["Марія купила книгу у магазині."],
        "rubric": ["Correct word order and case."],
        "tags": ["word_order"],
    }
    candidate.update(overrides)
    return candidate


def feedback(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "verdict": "partial",
        "corrected_answer": "книгу",
        "severity": "low",
        "confidence": "medium",
        "error_spans": [
            {"text": "книга", "tag": "case", "severity": "low", "explanation": "Use accusative."}
        ],
        "explanation": "Close. Use the accusative case for the object.",
        "next_drill_hint": "Practice the accusative case once.",
    }
    payload.update(overrides)
    return payload


def record_payload(exercise_id: str, modality: str = "reading", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "exercise_id": exercise_id,
        "modality": modality,
        "learner_response": "книга",
        "response_status": "completed",
        "candidate_feedback": feedback(),
        "score_metadata": {"questions_total": 2, "questions_correct": 1},
        "exercise_summary": "Short learner-safe summary.",
    }
    payload.update(overrides)
    return payload
