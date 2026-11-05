"""codeeval — a harness for evaluating AI-generated code the way a reviewer would.

Given a *task* (a problem statement, a hidden test suite) and one or more
*candidate* solutions (typically produced by an LLM), the harness:

1. runs every candidate against the tests in an isolated subprocess,
2. performs static analysis (complexity, nesting, smells, style),
3. scores each candidate on a weighted rubric
   (correctness, robustness, efficiency, maintainability),
4. optionally asks an LLM judge for a second opinion, and
5. writes a Markdown + JSON report with reviewer-style feedback.
"""

from codeeval.rubric import Scores, Weights, score_candidate
from codeeval.runner import RunResult, TestResult, run_candidate
from codeeval.static import StaticReport, analyze_source

__all__ = [
    "RunResult",
    "Scores",
    "StaticReport",
    "TestResult",
    "Weights",
    "analyze_source",
    "run_candidate",
    "score_candidate",
]

__version__ = "0.1.0"
