"""The evaluation pipeline: discover tasks, run candidates, score, collect feedback."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from codeeval.feedback import Remark, build_feedback
from codeeval.judge import Judge
from codeeval.rubric import Scores, Weights, score_candidate
from codeeval.runner import RunResult, run_candidate
from codeeval.static import StaticReport, Thresholds, analyze_source

log = logging.getLogger("codeeval")


@dataclass
class Task:
    name: str
    path: Path
    statement: str
    tests_path: Path
    candidates: list[Path]


@dataclass
class CandidateEvaluation:
    task: str
    candidate: str
    run: RunResult
    static: StaticReport
    scores: Scores
    feedback: list[Remark]
    judge_rationale: str | None = None

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "candidate": self.candidate,
            "scores": self.scores.to_dict(),
            "verdict": self.scores.verdict,
            "feedback": [{"category": r.category, "text": r.text} for r in self.feedback],
            "judge_rationale": self.judge_rationale,
            "run": self.run.to_dict(),
            "static": self.static.to_dict(),
        }


@dataclass
class TaskEvaluation:
    task: Task
    candidates: list[CandidateEvaluation] = field(default_factory=list)

    def ranked(self) -> list[CandidateEvaluation]:
        return sorted(self.candidates, key=lambda c: (-c.scores.overall, c.candidate))


def discover_tasks(tasks_dir: Path | str) -> list[Task]:
    """Each sub-directory with ``tests.py`` and a ``candidates/`` folder is a task."""
    tasks_dir = Path(tasks_dir)
    tasks: list[Task] = []
    for path in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        tests_path = path / "tests.py"
        cand_dir = path / "candidates"
        if not tests_path.exists() or not cand_dir.is_dir():
            continue
        statement_path = path / "task.md"
        statement = statement_path.read_text(encoding="utf-8") if statement_path.exists() else ""
        candidates = sorted(cand_dir.glob("*.py"))
        if candidates:
            tasks.append(Task(path.name, path, statement, tests_path, candidates))
    return tasks


def evaluate_task(
    task: Task,
    *,
    weights: Weights | None = None,
    thresholds: Thresholds | None = None,
    per_test_timeout_s: float = 5.0,
    use_ruff: bool = False,
    judge: Judge | None = None,
    judge_weight: float = 0.3,
) -> TaskEvaluation:
    runs: dict[Path, RunResult] = {}
    statics: dict[Path, StaticReport] = {}

    for cand in task.candidates:
        log.info("running %s/%s", task.name, cand.stem)
        runs[cand] = run_candidate(cand, task.tests_path, per_test_timeout_s=per_test_timeout_s)
        statics[cand] = analyze_source(cand.read_text(encoding="utf-8"), thresholds=thresholds, use_ruff=use_ruff)

    # Only fully passing candidates set the pace for the efficiency comparison;
    # a wrong-but-fast solution should not make correct ones look slow.
    clean = [r for r in runs.values() if r.ok and r.pass_rate() == 1.0 and r.total_test_time_s > 0]
    fastest = min((r.total_test_time_s for r in clean), default=None)

    evaluation = TaskEvaluation(task)
    for cand in task.candidates:
        run, static = runs[cand], statics[cand]
        judge_score = rationale = None
        if judge is not None:
            jr = judge.judge(task.statement, cand.read_text(encoding="utf-8"), run)
            judge_score, rationale = jr.score, jr.rationale
        scores = score_candidate(
            run, static, fastest_time_s=fastest, weights=weights, judge=judge_score, judge_weight=judge_weight
        )
        evaluation.candidates.append(
            CandidateEvaluation(
                task.name, cand.stem, run, static, scores, build_feedback(run, static, scores), rationale
            )
        )
    return evaluation


def evaluate_all(tasks: list[Task], **kwargs) -> list[TaskEvaluation]:
    return [evaluate_task(t, **kwargs) for t in tasks]
