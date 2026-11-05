"""Command-line interface.

python -m codeeval evaluate tasks/ --out reports/
python -m codeeval evaluate tasks/ --task two_sum --ruff
python -m codeeval evaluate tasks/ --llm-judge            # needs ANTHROPIC_API_KEY
python -m codeeval list tasks/
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from codeeval.evaluate import discover_tasks, evaluate_all
from codeeval.report import write_reports
from codeeval.rubric import Weights


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="codeeval", description="Evaluate AI-generated code like a reviewer would.")
    sub = p.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="run candidates against tests and write a report")
    ev.add_argument("tasks_dir", type=Path, help="directory containing task folders")
    ev.add_argument("--out", type=Path, default=Path("reports"), help="output directory (default: reports/)")
    ev.add_argument("--task", action="append", help="only evaluate this task (repeatable)")
    ev.add_argument("--timeout", type=float, default=5.0, help="per-test timeout in seconds")
    ev.add_argument("--ruff", action="store_true", help="also count ruff findings if ruff is installed")
    ev.add_argument("--llm-judge", action="store_true", help="add an LLM judge score (Anthropic API)")
    ev.add_argument("--judge-model", default="claude-sonnet-4-5")
    ev.add_argument("--judge-weight", type=float, default=0.3)
    ev.add_argument(
        "--weights",
        default=None,
        help="correctness,robustness,efficiency,maintainability e.g. 0.5,0.2,0.1,0.2",
    )
    ev.add_argument("-v", "--verbose", action="store_true")

    ls = sub.add_parser("list", help="list discovered tasks and candidates")
    ls.add_argument("tasks_dir", type=Path)
    return p


def _parse_weights(spec: str | None) -> Weights | None:
    if not spec:
        return None
    parts = [float(x) for x in spec.split(",")]
    if len(parts) != 4:
        raise SystemExit("--weights needs exactly four comma-separated numbers")
    return Weights(*parts)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if getattr(args, "verbose", False) else logging.WARNING, format="%(message)s"
    )

    tasks = discover_tasks(args.tasks_dir)
    if not tasks:
        print(f"no tasks found under {args.tasks_dir}", file=sys.stderr)
        return 2

    if args.command == "list":
        for t in tasks:
            print(f"{t.name}: {len(t.candidates)} candidate(s) — {', '.join(c.stem for c in t.candidates)}")
        return 0

    if args.task:
        tasks = [t for t in tasks if t.name in set(args.task)]
        if not tasks:
            print("none of the requested tasks were found", file=sys.stderr)
            return 2

    judge = None
    if args.llm_judge:
        from codeeval.judge import LLMJudge, anthropic_complete

        judge = LLMJudge(anthropic_complete(model=args.judge_model))

    evaluations = evaluate_all(
        tasks,
        weights=_parse_weights(args.weights),
        per_test_timeout_s=args.timeout,
        use_ruff=args.ruff,
        judge=judge,
        judge_weight=args.judge_weight,
    )
    md_path, json_path = write_reports(evaluations, args.out)

    for ev in evaluations:
        print(f"\n{ev.task.name}")
        for rank, c in enumerate(ev.ranked(), start=1):
            print(f"  {rank}. {c.candidate:<16} {c.scores.overall:5.1f}  {c.scores.grade}  {c.scores.verdict}")
    print(f"\nwrote {md_path} and {json_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
