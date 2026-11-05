"""Turn raw findings into the kind of feedback a reviewer would leave on a PR.

The goal is actionable, specific sentences — "test_edge_empty fails: expected
[] got None" — rather than a bare number. Each line is tagged with a category so
reports (or a model being trained on this feedback) can group them.
"""

from __future__ import annotations

from dataclasses import dataclass

from codeeval.rubric import Scores
from codeeval.runner import RunResult
from codeeval.static import StaticReport


@dataclass
class Remark:
    category: str  # correctness | robustness | efficiency | maintainability | blocking
    text: str

    def __str__(self) -> str:
        return f"[{self.category}] {self.text}"


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def build_feedback(run: RunResult, static: StaticReport, scores: Scores) -> list[Remark]:
    remarks: list[Remark] = []

    # --- blocking problems -------------------------------------------------
    if static.syntax_error:
        remarks.append(Remark("blocking", f"Does not parse: {static.syntax_error}."))
    if run.candidate_import_error:
        remarks.append(Remark("blocking", f"Importing the solution raised: {_first_line(run.candidate_import_error)}"))
    if run.tests_import_error:
        remarks.append(
            Remark("blocking", f"The test module could not be imported: {_first_line(run.tests_import_error)}")
        )
    if run.crashed:
        remarks.append(Remark("blocking", f"Run aborted: {run.crashed}"))
    if remarks:
        return remarks

    # --- correctness / robustness / efficiency -------------------------------
    labels = {"core": "correctness", "edge": "robustness", "perf": "efficiency"}
    for category, label in labels.items():
        failing = [t for t in run.by_category(category) if not t.passed]
        for t in failing:
            detail = f" — {t.message}" if t.message else ""
            remarks.append(Remark(label, f"`{t.name}` {t.status}{detail}"))

    perf_tests = run.by_category("perf")
    if perf_tests and all(t.passed for t in perf_tests):
        remarks.append(Remark("efficiency", f"All {len(perf_tests)} performance test(s) pass within the time limit."))

    # --- maintainability -------------------------------------------------------
    for issue in static.issues:
        remarks.append(Remark("maintainability", f"L{issue.lineno} {issue.code}: {issue.message}"))
    hot = [f for f in static.functions if f.complexity > 10]
    for f in hot:
        where = f"`{f.name}` (complexity {f.complexity}, {f.length} lines)"
        remarks.append(Remark("maintainability", f"{where} would be easier to review split into smaller functions."))

    # --- summary line ------------------------------------------------------------
    remarks.append(Remark("summary", summary_sentence(run, static, scores)))
    return remarks


def summary_sentence(run: RunResult, static: StaticReport, scores: Scores) -> str:
    core = run.by_category("core")
    edge = run.by_category("edge")
    parts = [f"{sum(t.passed for t in core)}/{len(core)} core tests pass"]
    if edge:
        parts.append(f"{sum(t.passed for t in edge)}/{len(edge)} edge-case tests pass")
    findings = len(static.issues)
    parts.append(f"{findings} static finding{'s' if findings != 1 else ''}")
    parts.append(f"max complexity {static.max_complexity}")
    body = ", ".join(parts)
    if scores.verdict == "Accept":
        tail = "Ready to merge."
    elif scores.verdict == "Revise":
        tail = "Close — fix the failing cases and address the findings before merging."
    else:
        tail = "Not mergeable in its current form."
    return f"{body}. {tail}"
