"""Static analysis of a candidate solution using the standard-library ``ast``.

We deliberately implement the metrics ourselves rather than depend on a
third-party linter, so the harness runs anywhere Python runs. If ``ruff`` is
installed it can be used as an additional signal (``use_ruff=True``).

Metrics per function
    * cyclomatic complexity (McCabe): 1 + decision points
    * length in lines, maximum nesting depth, parameter count, docstring

Issues (code → severity)
    E001 bare ``except:``                       error
    E012 use of ``eval`` / ``exec``             error
    W002 exception swallowed (``except: pass``) warn
    W003 mutable default argument               warn
    W004 complexity above threshold             warn
    W005 function longer than threshold         warn
    W006 nesting deeper than threshold          warn
    W008 unused import                          warn
    W010 too many parameters                    warn
    W011 ``global`` statement                   warn
    I007 public function without docstring      info
    I009 ``print`` call in library code         info
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field

SEVERITY = {"E": "error", "W": "warn", "I": "info"}


@dataclass
class Issue:
    code: str
    message: str
    lineno: int

    @property
    def severity(self) -> str:
        return SEVERITY[self.code[0]]


@dataclass
class FunctionMetrics:
    name: str
    lineno: int
    complexity: int
    length: int
    max_depth: int
    params: int
    has_docstring: bool


@dataclass
class Thresholds:
    complexity: int = 10
    length: int = 50
    depth: int = 4
    params: int = 6


@dataclass
class StaticReport:
    loc: int = 0
    functions: list[FunctionMetrics] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    syntax_error: str | None = None
    ruff_issue_count: int | None = None

    @property
    def max_complexity(self) -> int:
        return max((f.complexity for f in self.functions), default=0)

    def count(self, severity: str) -> int:
        return sum(1 for i in self.issues if i.severity == severity)

    def to_dict(self) -> dict:
        d = asdict(self)
        for issue, raw in zip(self.issues, d["issues"], strict=True):
            raw["severity"] = issue.severity
        d["max_complexity"] = self.max_complexity
        return d


# --------------------------------------------------------------------------
# complexity / nesting
# --------------------------------------------------------------------------

_DECISION_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.IfExp,
    ast.Assert,
)
_NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)


def cyclomatic_complexity(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """McCabe complexity: 1 + branches, boolean operators, comprehension filters, match cases."""
    score = 1
    for node in ast.walk(fn):
        if isinstance(node, _DECISION_NODES):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            score += 1 + len(node.ifs)
        elif isinstance(node, ast.match_case):
            score += 1
    return score


def max_nesting_depth(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    def _depth(node: ast.AST, current: int) -> int:
        deepest = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue  # nested defs are measured separately
            nxt = current + 1 if isinstance(child, _NESTING_NODES) else current
            deepest = max(deepest, _depth(child, nxt))
        return deepest

    return _depth(fn, 0)


def _function_length(fn: ast.AST) -> int:
    end = getattr(fn, "end_lineno", fn.lineno)
    return end - fn.lineno + 1


def _param_count(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    a = fn.args
    names = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return len([n for n in names if n not in ("self", "cls")])


# --------------------------------------------------------------------------
# issue detection
# --------------------------------------------------------------------------

_MUTABLE_DEFAULTS = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)


class _IssueCollector(ast.NodeVisitor):
    def __init__(self, thresholds: Thresholds):
        self.t = thresholds
        self.issues: list[Issue] = []
        self.functions: list[FunctionMetrics] = []
        self.imported: dict[str, int] = {}
        self.used_names: set[str] = set()
        self._class_depth = 0

    # ---- imports / names -------------------------------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imported[(alias.asname or alias.name).split(".")[0]] = node.lineno

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name != "*":
                self.imported[alias.asname or alias.name] = node.lineno

    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        self.generic_visit(node)

    # ---- statements ------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def visit_Global(self, node: ast.Global):
        self.issues.append(
            Issue("W011", f"`global {', '.join(node.names)}` makes state hard to reason about", node.lineno)
        )

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.type is None:
            self.issues.append(Issue("E001", "bare `except:` also catches KeyboardInterrupt/SystemExit", node.lineno))
        body = node.body
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            self.issues.append(Issue("W002", "exception is swallowed silently (`except ...: pass`)", node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                self.issues.append(
                    Issue("E012", f"`{node.func.id}` on runtime data is a code-injection risk", node.lineno)
                )
            elif node.func.id == "print":
                self.issues.append(
                    Issue("I009", "`print` in library code; prefer returning values or logging", node.lineno)
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        metrics = FunctionMetrics(
            name=node.name,
            lineno=node.lineno,
            complexity=cyclomatic_complexity(node),
            length=_function_length(node),
            max_depth=max_nesting_depth(node),
            params=_param_count(node),
            has_docstring=ast.get_docstring(node) is not None,
        )
        self.functions.append(metrics)

        for default in node.args.defaults + node.args.kw_defaults:
            if isinstance(default, _MUTABLE_DEFAULTS):
                self.issues.append(Issue("W003", f"`{node.name}` has a mutable default argument", default.lineno))
        if metrics.complexity > self.t.complexity:
            self.issues.append(
                Issue("W004", f"`{node.name}` complexity {metrics.complexity} > {self.t.complexity}", node.lineno)
            )
        if metrics.length > self.t.length:
            self.issues.append(
                Issue("W005", f"`{node.name}` is {metrics.length} lines (> {self.t.length})", node.lineno)
            )
        if metrics.max_depth > self.t.depth:
            self.issues.append(
                Issue("W006", f"`{node.name}` nests {metrics.max_depth} levels deep (> {self.t.depth})", node.lineno)
            )
        if metrics.params > self.t.params:
            self.issues.append(
                Issue("W010", f"`{node.name}` takes {metrics.params} parameters (> {self.t.params})", node.lineno)
            )
        is_public = not node.name.startswith("_")
        if is_public and not metrics.has_docstring and self._class_depth == 0:
            self.issues.append(Issue("I007", f"public function `{node.name}` has no docstring", node.lineno))
        self.generic_visit(node)

    def finish(self):
        for name, lineno in self.imported.items():
            if name not in self.used_names:
                self.issues.append(Issue("W008", f"import `{name}` is unused", lineno))
        self.issues.sort(key=lambda i: (i.lineno, i.code))


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------


def analyze_source(source: str, *, thresholds: Thresholds | None = None, use_ruff: bool = False) -> StaticReport:
    """Analyse Python ``source`` and return a :class:`StaticReport`."""
    thresholds = thresholds or Thresholds()
    report = StaticReport(loc=sum(1 for line in source.splitlines() if line.strip()))
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.syntax_error = f"line {exc.lineno}: {exc.msg}"
        return report

    collector = _IssueCollector(thresholds)
    collector.visit(tree)
    collector.finish()
    report.functions = collector.functions
    report.issues = collector.issues

    if use_ruff:
        report.ruff_issue_count = _ruff_issue_count(source)
    return report


def _ruff_issue_count(source: str) -> int | None:
    ruff = shutil.which("ruff")
    if not ruff:
        return None
    try:
        proc = subprocess.run(
            [ruff, "check", "--output-format", "json", "--quiet", "-"],
            input=source,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return len(json.loads(proc.stdout or "[]"))
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None
