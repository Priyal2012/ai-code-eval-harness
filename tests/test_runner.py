from pathlib import Path

from codeeval.runner import run_candidate

TESTS = """
from solution import add

def test_add():
    assert add(1, 2) == 3

def test_edge_negative():
    assert add(-1, -1) == -2

def test_perf_loop():
    assert add(0, 0) == 0
"""


def _write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_all_pass(tmp_path):
    cand = _write(tmp_path, "good.py", "def add(a, b):\n    return a + b\n")
    tests = _write(tmp_path, "tests.py", TESTS)
    run = run_candidate(cand, tests)
    assert run.ok
    assert run.pass_rate() == 1.0
    assert {t.category for t in run.tests} == {"core", "edge", "perf"}
    assert run.candidate == "good"


def test_failure_and_error_are_distinguished(tmp_path):
    cand = _write(
        tmp_path, "bad.py", "def add(a, b):\n    if a < 0:\n        raise RuntimeError('boom')\n    return a - b\n"
    )
    tests = _write(tmp_path, "tests.py", TESTS)
    run = run_candidate(cand, tests)
    statuses = {t.name: t.status for t in run.tests}
    assert statuses["test_add"] == "failed"
    assert statuses["test_edge_negative"] == "error"
    assert "RuntimeError" in next(t.message for t in run.tests if t.name == "test_edge_negative")


def test_candidate_import_error(tmp_path):
    cand = _write(tmp_path, "broken.py", "def add(a, b:\n    return a + b\n")
    tests = _write(tmp_path, "tests.py", TESTS)
    run = run_candidate(cand, tests)
    assert not run.ok
    assert "SyntaxError" in run.candidate_import_error
    assert run.tests == []


def test_per_test_timeout(tmp_path):
    cand = _write(tmp_path, "slow.py", "import time\ndef add(a, b):\n    time.sleep(3)\n    return a + b\n")
    tests = _write(tmp_path, "tests.py", "from solution import add\n\ndef test_add():\n    assert add(1, 2) == 3\n")
    run = run_candidate(cand, tests, per_test_timeout_s=0.5)
    assert run.tests[0].status == "timeout"


def test_candidate_stdout_noise_is_ignored(tmp_path):
    cand = _write(tmp_path, "noisy.py", "print('{not json')\nprint('hello')\ndef add(a, b):\n    return a + b\n")
    tests = _write(tmp_path, "tests.py", TESTS)
    run = run_candidate(cand, tests)
    assert run.ok and run.pass_rate() == 1.0
