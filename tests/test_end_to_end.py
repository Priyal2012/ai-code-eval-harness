"""Runs the bundled tasks end to end and checks the harness ranks them sensibly."""

import json
from pathlib import Path

import pytest

from codeeval.cli import main
from codeeval.evaluate import discover_tasks, evaluate_task

TASKS_DIR = Path(__file__).resolve().parents[1] / "tasks"


def test_discovers_bundled_tasks():
    names = [t.name for t in discover_tasks(TASKS_DIR)]
    assert names == ["lru_cache", "merge_intervals", "parse_log_line", "two_sum"]
    assert all(len(t.candidates) == 3 for t in discover_tasks(TASKS_DIR))


@pytest.mark.parametrize("task_name", ["two_sum", "lru_cache", "parse_log_line", "merge_intervals"])
def test_reference_candidate_wins(task_name):
    task = next(t for t in discover_tasks(TASKS_DIR) if t.name == task_name)
    ev = evaluate_task(task, per_test_timeout_s=5.0)
    ranked = ev.ranked()
    assert ranked[0].candidate == "candidate_a", [(c.candidate, c.scores.overall) for c in ranked]
    assert ranked[0].scores.verdict == "Accept"
    assert ranked[0].scores.correctness == 1.0
    assert all(c.scores.overall < ranked[0].scores.overall for c in ranked[1:])


def test_cli_writes_reports(tmp_path):
    out = tmp_path / "reports"
    code = main(["evaluate", str(TASKS_DIR), "--task", "two_sum", "--out", str(out)])
    assert code == 0
    md = (out / "report.md").read_text()
    data = json.loads((out / "report.json").read_text())
    assert "## Task: `two_sum`" in md
    assert "Reviewer notes" in md
    assert data["tasks"][0]["candidates"][0]["candidate"] == "candidate_a"
    assert data["tasks"][0]["candidates"][0]["verdict"] == "Accept"


def test_cli_list(capsys):
    assert main(["list", str(TASKS_DIR)]) == 0
    assert "two_sum: 3 candidate(s)" in capsys.readouterr().out
