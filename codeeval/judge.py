"""Optional LLM-as-judge second opinion.

The judge is deliberately decoupled from any vendor SDK: ``LLMJudge`` takes a
``complete(prompt) -> str`` callable, so it can be driven by any model — or by a
stub in tests. ``anthropic_complete`` builds such a callable for the Anthropic
Messages API using only ``requests``.

The judge sees the task statement, the candidate source and the *test outcomes*
(so it cannot hallucinate correctness), and returns a 0–1 score with a rationale.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from codeeval.runner import RunResult

Completer = Callable[[str], str]


@dataclass
class JudgeResult:
    score: float  # 0-1
    rationale: str
    raw: str = ""


class Judge(Protocol):
    def judge(self, task_text: str, source: str, run: RunResult) -> JudgeResult: ...


_PROMPT = """You are a senior software engineer reviewing a code submission.

## Task
{task}

## Submission
```python
{source}
```

## Test outcomes (ground truth — do not contradict these)
{outcomes}

Review the submission as you would in a pull request. Consider correctness
(given the test outcomes), handling of edge cases, efficiency for realistic
input sizes, readability, naming, and idiomatic use of the language.

Respond with ONLY a JSON object of the form
{{"score": <number between 0 and 1>, "rationale": "<two to four sentences>"}}
"""


class LLMJudge:
    """Scores a candidate with an LLM. ``complete`` maps a prompt to the model's reply."""

    def __init__(self, complete: Completer):
        self._complete = complete

    def judge(self, task_text: str, source: str, run: RunResult) -> JudgeResult:
        outcomes = "\n".join(f"- {t.name}: {t.status}{' — ' + t.message if t.message else ''}" for t in run.tests)
        if run.candidate_import_error:
            outcomes = f"- solution failed to import: {run.candidate_import_error.strip().splitlines()[-1]}"
        prompt = _PROMPT.format(task=task_text.strip(), source=source.rstrip(), outcomes=outcomes or "- (no tests ran)")
        raw = self._complete(prompt)
        return parse_judge_reply(raw)


def parse_judge_reply(raw: str) -> JudgeResult:
    """Extract ``{"score": .., "rationale": ..}`` from a model reply, tolerating prose around it."""
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return JudgeResult(0.0, "judge reply contained no JSON", raw)
    try:
        data = json.loads(match.group(0))
        score = float(data.get("score", 0.0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JudgeResult(0.0, "judge reply was not valid JSON", raw)
    score = min(1.0, max(0.0, score))
    return JudgeResult(score, str(data.get("rationale", "")).strip(), raw)


def anthropic_complete(model: str = "claude-sonnet-4-5", max_tokens: int = 600) -> Completer:
    """Return a completer that calls the Anthropic Messages API via ``requests``.

    Requires ``ANTHROPIC_API_KEY`` in the environment. Imported lazily so the
    rest of the harness has no network dependency.
    """
    import requests  # noqa: WPS433 - optional dependency

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    def _complete(prompt: str) -> str:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        blocks = resp.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")

    return _complete
