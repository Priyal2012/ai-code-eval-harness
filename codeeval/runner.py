"""Run a candidate solution against a task's test suite in an isolated subprocess.

Isolation here means: a fresh interpreter (``python -I``), a temporary working
directory, a wall-clock timeout per test and for the whole run, and an
address-space limit on Linux. It is *not* a security sandbox — run untrusted
code inside a container if you need real containment.

A task's ``tests.py`` is a plain module of ``test_*`` functions that import the
candidate as ``solution``. Test names carry their category:

* ``test_<name>``        core correctness
* ``test_edge_<name>``   edge cases / robustness
* ``test_perf_<name>``   performance (large inputs, should finish within the limit)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Driver executed inside the sandboxed interpreter. It is written as a string so
# that the subprocess only ever needs the two files we copy next to it.
_DRIVER = r'''
import importlib, json, signal, sys, time, traceback

PER_TEST_TIMEOUT = float(sys.argv[1])
sys.path.insert(0, ".")
out = {"candidate_import_error": None, "tests_import_error": None, "results": []}


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _failing_line(exc):
    """For a bare `assert`, report the source line that failed."""
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename.endswith("tests.py")]
    if frames and frames[-1].line:
        return "assertion failed: `" + frames[-1].line.strip() + "`"
    return "assertion failed"


try:
    importlib.import_module("solution")
except BaseException:
    out["candidate_import_error"] = traceback.format_exc()[-2000:]
    print(json.dumps(out))
    sys.exit(0)

try:
    tests = importlib.import_module("tests")
except BaseException:
    out["tests_import_error"] = traceback.format_exc()[-2000:]
    print(json.dumps(out))
    sys.exit(0)

names = sorted(n for n in dir(tests) if n.startswith("test_") and callable(getattr(tests, n)))
has_alarm = hasattr(signal, "SIGALRM")
if has_alarm:
    signal.signal(signal.SIGALRM, _alarm)

for name in names:
    fn = getattr(tests, name)
    t0 = time.perf_counter()
    if has_alarm:
        signal.setitimer(signal.ITIMER_REAL, PER_TEST_TIMEOUT)
    try:
        fn()
        status, msg = "passed", ""
    except _Timeout:
        status, msg = "timeout", f"exceeded {PER_TEST_TIMEOUT:.1f}s"
    except AssertionError as e:
        status, msg = "failed", str(e) or _failing_line(e)
    except BaseException as e:  # noqa: BLE001 - we want to report anything
        status, msg = "error", f"{type(e).__name__}: {e}"
    finally:
        if has_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)
    out["results"].append(
        {"name": name, "status": status, "message": msg[:500], "duration_s": time.perf_counter() - t0}
    )

print(json.dumps(out))
'''


@dataclass
class TestResult:
    """Outcome of one ``test_*`` function."""

    __test__ = False  # keep pytest from trying to collect this dataclass

    name: str
    status: str  # passed | failed | error | timeout
    message: str = ""
    duration_s: float = 0.0

    @property
    def category(self) -> str:
        if self.name.startswith("test_edge_"):
            return "edge"
        if self.name.startswith("test_perf_"):
            return "perf"
        return "core"

    @property
    def passed(self) -> bool:
        return self.status == "passed"


@dataclass
class RunResult:
    """Everything we learned from executing one candidate."""

    candidate: str
    tests: list[TestResult] = field(default_factory=list)
    candidate_import_error: str | None = None
    tests_import_error: str | None = None
    crashed: str | None = None  # harness-level failure (e.g. whole-run timeout)
    wall_time_s: float = 0.0

    # -- convenience -------------------------------------------------------
    def by_category(self, category: str) -> list[TestResult]:
        return [t for t in self.tests if t.category == category]

    def pass_rate(self, category: str | None = None) -> float | None:
        """Fraction of tests passed in ``category`` (all if None). None if no tests."""
        pool = self.tests if category is None else self.by_category(category)
        if not pool:
            return None
        return sum(t.passed for t in pool) / len(pool)

    @property
    def total_test_time_s(self) -> float:
        return sum(t.duration_s for t in self.tests)

    @property
    def ok(self) -> bool:
        return not (self.candidate_import_error or self.tests_import_error or self.crashed)

    def to_dict(self) -> dict:
        return asdict(self)


def _limit_resources(max_memory_mb: int):
    """Return a preexec_fn that caps the child's address space (POSIX only)."""
    try:
        import resource  # noqa: WPS433 - POSIX only
    except ImportError:  # pragma: no cover - Windows
        return None

    def _apply():
        limit = max_memory_mb * 1024 * 1024
        try:
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        except (ValueError, OSError):
            pass

    return _apply


def run_candidate(
    candidate_path: Path | str,
    tests_path: Path | str,
    *,
    per_test_timeout_s: float = 5.0,
    total_timeout_s: float | None = None,
    max_memory_mb: int = 512,
    python: str | None = None,
) -> RunResult:
    """Execute ``candidate_path`` against ``tests_path`` and return a :class:`RunResult`."""
    candidate_path = Path(candidate_path)
    tests_path = Path(tests_path)
    result = RunResult(candidate=candidate_path.stem)
    python = python or sys.executable
    total_timeout_s = total_timeout_s or per_test_timeout_s * 20

    with tempfile.TemporaryDirectory(prefix="codeeval-") as tmp:
        tmpdir = Path(tmp)
        shutil.copy(candidate_path, tmpdir / "solution.py")
        shutil.copy(tests_path, tmpdir / "tests.py")
        (tmpdir / "_driver.py").write_text(_DRIVER, encoding="utf-8")

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [python, "-I", "_driver.py", str(per_test_timeout_s)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=total_timeout_s,
                preexec_fn=_limit_resources(max_memory_mb) if sys.platform != "win32" else None,
            )
        except subprocess.TimeoutExpired:
            result.crashed = f"whole run exceeded {total_timeout_s:.0f}s"
            result.wall_time_s = time.perf_counter() - t0
            return result
        result.wall_time_s = time.perf_counter() - t0

    payload = _last_json_line(proc.stdout)
    if payload is None:
        tail = (proc.stderr or proc.stdout or "")[-1500:]
        result.crashed = f"driver produced no result (exit {proc.returncode}): {tail}"
        return result

    result.candidate_import_error = payload.get("candidate_import_error")
    result.tests_import_error = payload.get("tests_import_error")
    result.tests = [TestResult(**r) for r in payload.get("results", [])]
    return result


def _last_json_line(stdout: str) -> dict | None:
    """The driver prints one JSON object; candidates may print noise before it."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None
