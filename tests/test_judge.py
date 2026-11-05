from codeeval.judge import LLMJudge, parse_judge_reply
from codeeval.runner import RunResult, TestResult


def test_parse_tolerates_prose_around_json():
    res = parse_judge_reply('Sure! Here you go:\n{"score": 0.8, "rationale": "Clean and correct."}\nThanks.')
    assert res.score == 0.8
    assert res.rationale == "Clean and correct."


def test_parse_clamps_and_handles_garbage():
    assert parse_judge_reply('{"score": 7, "rationale": "x"}').score == 1.0
    assert parse_judge_reply("no json here").score == 0.0


def test_llm_judge_includes_test_outcomes_in_prompt():
    seen = {}

    def fake_complete(prompt: str) -> str:
        seen["prompt"] = prompt
        return '{"score": 0.6, "rationale": "Fails an edge case."}'

    run = RunResult(candidate="c", tests=[TestResult("test_edge_x", "failed", "expected [] got None")])
    result = LLMJudge(fake_complete).judge("# task", "def f(): pass", run)
    assert result.score == 0.6
    assert "test_edge_x: failed" in seen["prompt"]
    assert "def f(): pass" in seen["prompt"]
