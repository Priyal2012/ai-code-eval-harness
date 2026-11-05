"""Turn execution results and static analysis into rubric scores.

Four dimensions, each in ``[0, 1]``:

correctness     share of *core* tests passed
robustness      share of *edge* tests passed (falls back to correctness if a task has none)
efficiency      share of *perf* tests passed, blended with runtime relative to the
                fastest candidate on the same task
maintainability 1.0 minus penalties for static-analysis findings and complexity

The weighted sum (×100) is the overall score. Weights are configurable; the
defaults reflect what a reviewer cares about first: does it work, does it
survive edge cases, then how it is written.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from codeeval.runner import RunResult
from codeeval.static import StaticReport


@dataclass(frozen=True)
class Weights:
    correctness: float = 0.45
    robustness: float = 0.20
    efficiency: float = 0.15
    maintainability: float = 0.20

    def __post_init__(self):
        total = self.correctness + self.robustness + self.efficiency + self.maintainability
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total:.3f}")


PENALTY = {"error": 0.25, "warn": 0.10, "info": 0.03}


@dataclass
class Scores:
    correctness: float
    robustness: float
    efficiency: float
    maintainability: float
    overall: float  # 0-100
    grade: str
    verdict: str  # Accept | Revise | Reject
    judge: float | None = None  # optional LLM judge score in [0, 1]

    def to_dict(self) -> dict:
        return asdict(self)


def letter_grade(overall: float) -> str:
    for threshold, letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if overall >= threshold:
            return letter
    return "F"


def maintainability_score(static: StaticReport) -> float:
    """1.0 for clean code; each finding subtracts according to its severity."""
    if static.syntax_error:
        return 0.0
    score = 1.0
    for issue in static.issues:
        score -= PENALTY[issue.severity]
    if static.max_complexity > 15:
        score -= 0.20
    if static.ruff_issue_count:
        score -= min(0.3, 0.02 * static.ruff_issue_count)
    return max(0.0, round(score, 4))


def efficiency_score(run: RunResult, fastest_time_s: float | None) -> float:
    perf = run.pass_rate("perf")
    if fastest_time_s and run.total_test_time_s > 0:
        relative = min(1.0, fastest_time_s / run.total_test_time_s)
    else:
        relative = 1.0
    if perf is None:
        return round(relative, 4)
    return round(0.7 * perf + 0.3 * relative, 4)


def verdict_for(correctness: float, robustness: float, static: StaticReport, run: RunResult) -> str:
    if not run.ok:
        return "Reject"
    perf = run.pass_rate("perf")
    perf_ok = perf is None or perf == 1.0
    if correctness == 1.0 and robustness >= 0.8 and perf_ok and static.count("error") == 0:
        return "Accept"
    if correctness >= 0.6:
        return "Revise"
    return "Reject"


def score_candidate(
    run: RunResult,
    static: StaticReport,
    *,
    fastest_time_s: float | None = None,
    weights: Weights | None = None,
    judge: float | None = None,
    judge_weight: float = 0.3,
) -> Scores:
    """Combine a :class:`RunResult` and :class:`StaticReport` into :class:`Scores`."""
    weights = weights or Weights()

    if not run.ok:
        # Could not even import or execute: nothing to reward.
        return Scores(
            0.0, 0.0, 0.0, maintainability_score(static) if not static.syntax_error else 0.0, 0.0, "F", "Reject", judge
        )

    correctness = run.pass_rate("core")
    correctness = 0.0 if correctness is None else correctness
    robustness = run.pass_rate("edge")
    robustness = correctness if robustness is None else robustness
    efficiency = efficiency_score(run, fastest_time_s)
    maintainability = maintainability_score(static)

    heuristic = (
        weights.correctness * correctness
        + weights.robustness * robustness
        + weights.efficiency * efficiency
        + weights.maintainability * maintainability
    )
    overall = heuristic if judge is None else (1 - judge_weight) * heuristic + judge_weight * judge
    overall = round(overall * 100, 1)

    return Scores(
        correctness=round(correctness, 4),
        robustness=round(robustness, 4),
        efficiency=efficiency,
        maintainability=maintainability,
        overall=overall,
        grade=letter_grade(overall),
        verdict=verdict_for(correctness, robustness, static, run),
        judge=judge,
    )
