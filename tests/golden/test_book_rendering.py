from __future__ import annotations

from language_tutor.book import render_lookup


def test_word_render_with_gloss_and_translation() -> None:
    assert render_lookup("word", "esquivo", {"translation": "evasive", "gloss": "adj"}) == "**esquivo** — adj (translation: evasive)"


def test_word_render_with_translation_only() -> None:
    assert render_lookup("word", "esquivo", {"translation": "evasive"}) == "**esquivo** (translation: evasive)"


def test_word_render_with_gloss_only() -> None:
    assert render_lookup("word", "esquivo", {"gloss": "adj"}) == "**esquivo** — adj"


def test_word_render_bare_when_no_translation_or_gloss() -> None:
    assert render_lookup("word", "esquivo", {"translation": ""}) == "**esquivo**"


def test_sentence_render() -> None:
    assert render_lookup("sentence", "Hola mundo.", {"translation": "Hello world."}) == "> Hola mundo.\n\nHello world."


def test_passage_render_falls_back_to_explanation() -> None:
    assert render_lookup("passage", "Long.", {"explanation": "Body."}) == "> Long.\n\nBody."


def test_question_render() -> None:
    assert render_lookup("question", "Why?", {"answer": "Because."}) == "Q: Why?\nA: Because."
