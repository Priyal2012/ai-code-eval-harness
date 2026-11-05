import pytest

from codeeval.rubric import Weights, letter_grade, maintainability_score, score_candidate
from codeeval.runner import RunResult, TestResult
from codeeval.static import Issue, StaticReport


def _run(**statuses: str) -> RunResult:
    return RunResult(candidate="x", tests=[TestResult(name=n, status=s, duration_s=0.01) for n, s in statuses.items()])


def test_perfect_candidate_scores_100():
    run = _run(test_a="passed", test_edge_b="passed", test_perf_c="passed")
    scores = score_candidate(run, StaticReport(), fastest_time_s=run.total_test_time_s)
    assert scores.overall == 100.0
    assert scores.grade == "A"
    assert scores.verdict == "Accept"


def test_import_failure_scores_zero():
    run = RunResult(candidate="x", candidate_import_error="SyntaxError: bad")
    scores = score_candidate(run, StaticReport(syntax_error="line 1: invalid syntax"))
    assert scores.overall == 0.0 and scores.verdict == "Reject"


def test_partial_correctness_is_revise():
    run = _run(test_a="passed", test_b="passed", test_c="failed", test_edge_d="passed")
    scores = score_candidate(run, StaticReport())
    assert 0.6 <= scores.correctness < 1.0
    assert scores.verdict == "Revise"


def test_robustness_falls_back_to_correctness_without_edge_tests():
    run = _run(test_a="passed", test_b="failed")
    scores = score_candidate(run, StaticReport())
    assert scores.robustness == scores.correctness == 0.5


def test_static_findings_reduce_maintainability():
    clean = maintainability_score(StaticReport())
    dirty = maintainability_score(StaticReport(issues=[Issue("E001", "bare except", 1), Issue("W003", "mutable", 2)]))
    assert clean == 1.0
    assert dirty == pytest.approx(1.0 - 0.25 - 0.10)


def test_error_finding_blocks_accept():
    run = _run(test_a="passed", test_edge_b="passed")
    scores = score_candidate(run, StaticReport(issues=[Issue("E001", "bare except", 1)]))
    assert scores.verdict == "Revise"


def test_judge_blends_into_overall():
    run = _run(test_a="passed", test_edge_b="passed")
    without = score_candidate(run, StaticReport())
    with_judge = score_candidate(run, StaticReport(), judge=0.5, judge_weight=0.5)
    assert without.overall == 100.0
    assert with_judge.overall == 75.0


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        Weights(0.5, 0.5, 0.5, 0.5)


@pytest.mark.parametrize("value,grade", [(95, "A"), (85, "B"), (72, "C"), (61, "D"), (12, "F")])
def test_letter_grade(value, grade):
    assert letter_grade(value) == grade
