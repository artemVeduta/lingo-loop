from __future__ import annotations

from tests.conftest import invoke_json


def test_writing_prompt_and_record(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk","interests":["food"]},"preferences":{}}',
        ],
    )
    prompt = invoke_json(runner, ["writing", "prompt", "--json"])
    assert "food" in prompt["prompt"]
    payload = '{"prompt_id":"p1","learner_answer":"x","candidate_feedback":{"verdict":"needs_review","corrected_answer":"x","severity":"low","confidence":"low","error_spans":[],"explanation":"Ok","next_drill_hint":"Try again."}}'
    result = invoke_json(runner, ["writing", "record", "--json", payload])
    assert result["persisted_mistakes"] == 0
