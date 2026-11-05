import ast
import textwrap

from codeeval.static import Thresholds, analyze_source, cyclomatic_complexity


def _fn(src: str):
    tree = ast.parse(textwrap.dedent(src))
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def test_complexity_straight_line_is_one():
    assert cyclomatic_complexity(_fn("def f():\n    return 1\n")) == 1


def test_complexity_counts_branches_and_boolops():
    src = """
    def f(x, y):
        if x and y:        # +1 if, +1 and
            return 1
        for i in range(3): # +1
            if i:          # +1
                pass
        return [i for i in x if i]  # +1 comprehension, +1 filter
    """
    assert cyclomatic_complexity(_fn(src)) == 1 + 2 + 1 + 1 + 2


def test_detects_common_smells():
    src = """
    import os
    import re

    def f(a, items=[]):
        try:
            return eval(a)
        except:
            pass
        print(re.escape(a))
    """
    report = analyze_source(textwrap.dedent(src))
    codes = {i.code for i in report.issues}
    assert {"E001", "E012", "W002", "W003", "W008", "I007", "I009"} <= codes
    unused = [i for i in report.issues if i.code == "W008"]
    assert len(unused) == 1 and "os" in unused[0].message


def test_thresholds_apply():
    src = "def f(a, b, c):\n" + "".join(f"    if a == {i}: return {i}\n" for i in range(12))
    report = analyze_source(src, thresholds=Thresholds(complexity=5, length=5, params=2))
    codes = {i.code for i in report.issues}
    assert {"W004", "W005", "W010"} <= codes


def test_syntax_error_is_reported_not_raised():
    report = analyze_source("def f(:\n    pass")
    assert report.syntax_error is not None
    assert report.functions == []


def test_nesting_depth():
    src = """
    def f(xs):
        for x in xs:
            if x:
                while x:
                    with open(x):
                        pass
        return 0
    """
    report = analyze_source(textwrap.dedent(src))
    assert report.functions[0].max_depth == 4


def test_methods_are_not_flagged_for_docstrings():
    src = "class C:\n    def go(self):\n        return 1\n"
    report = analyze_source(src)
    assert not [i for i in report.issues if i.code == "I007"]
    assert report.functions[0].params == 0
