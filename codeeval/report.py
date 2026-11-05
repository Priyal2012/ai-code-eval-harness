"""Render evaluations as Markdown (for humans) and JSON (for pipelines)."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from codeeval.evaluate import CandidateEvaluation, TaskEvaluation

_PCT = "{:.0%}"


def _pct(value: float) -> str:
    return _PCT.format(value)


def render_markdown(evaluations: list[TaskEvaluation], *, title: str = "Code evaluation report") -> str:
    lines: list[str] = [
        f"# {title}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]

    # ---- leaderboard across tasks ----------------------------------------------
    totals: dict[str, list[float]] = defaultdict(list)
    verdicts: dict[str, list[str]] = defaultdict(list)
    for ev in evaluations:
        for c in ev.candidates:
            totals[c.candidate].append(c.scores.overall)
            verdicts[c.candidate].append(c.scores.verdict)
    n_candidates = sum(len(ev.candidates) for ev in evaluations)
    lines += [
        "## Summary",
        "",
        f"{len(evaluations)} task(s), {n_candidates} candidate solution(s).",
        "",
        "| Candidate | Tasks | Mean score | Accept | Revise | Reject |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in sorted(totals, key=lambda n: -sum(totals[n]) / len(totals[n])):
        v = verdicts[name]
        lines.append(
            f"| {name} | {len(totals[name])} | {sum(totals[name]) / len(totals[name]):.1f} "
            f"| {v.count('Accept')} | {v.count('Revise')} | {v.count('Reject')} |"
        )
    lines.append("")

    # ---- per task ------------------------------------------------------------------
    for ev in evaluations:
        lines += [f"## Task: `{ev.task.name}`", ""]
        if ev.task.statement.strip():
            first = ev.task.statement.strip().splitlines()[0].lstrip("# ").strip()
            lines += [f"_{first}_", ""]
        lines += [
            "| Rank | Candidate | Overall | Grade | Verdict | Correctness | Robustness | Efficiency | Maintainability |"
            + (" Judge |" if any(c.scores.judge is not None for c in ev.candidates) else ""),
            "| ---: | --- | ---: | :-: | --- | ---: | ---: | ---: | ---: |"
            + (" ---: |" if any(c.scores.judge is not None for c in ev.candidates) else ""),
        ]
        for rank, c in enumerate(ev.ranked(), start=1):
            s = c.scores
            row = (
                f"| {rank} | `{c.candidate}` | **{s.overall:.1f}** | {s.grade} | {s.verdict} "
                f"| {_pct(s.correctness)} | {_pct(s.robustness)} | {_pct(s.efficiency)} | {_pct(s.maintainability)} |"
            )
            if s.judge is not None:
                row += f" {_pct(s.judge)} |"
            lines.append(row)
        lines.append("")
        for c in ev.ranked():
            lines += _candidate_section(c)
    return "\n".join(lines).rstrip() + "\n"


def _candidate_section(c: CandidateEvaluation) -> list[str]:
    out = [f"### `{c.candidate}` — {c.scores.overall:.1f} ({c.scores.verdict})", ""]
    summary = next((r for r in c.feedback if r.category == "summary"), None)
    if summary:
        out += [summary.text, ""]
    others = [r for r in c.feedback if r.category != "summary"]
    if others:
        out += ["**Reviewer notes**", ""]
        out += [f"- {r}" for r in others]
        out.append("")
    if c.judge_rationale:
        out += ["**LLM judge**", "", f"> {c.judge_rationale}", ""]
    return out


def to_json(evaluations: list[TaskEvaluation]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": [
            {
                "task": ev.task.name,
                "candidates": [c.to_dict() for c in ev.ranked()],
            }
            for ev in evaluations
        ],
    }


def write_reports(
    evaluations: list[TaskEvaluation], out_dir: Path | str, *, title: str = "Code evaluation report"
) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "report.md"
    json_path = out_dir / "report.json"
    md_path.write_text(render_markdown(evaluations, title=title), encoding="utf-8")
    json_path.write_text(json.dumps(to_json(evaluations), indent=2), encoding="utf-8")
    return md_path, json_path
