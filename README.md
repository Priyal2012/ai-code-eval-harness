# ai-code-eval-harness

**Evaluate AI-generated code the way a practicing engineer reviews a pull request.**

Large language models produce plausible-looking code that is often *almost* right:
it passes the happy path, fails an edge case, quietly degrades to O(n²), or swallows
exceptions. This harness takes a task and several candidate solutions and tells you —
with evidence — which one you would actually merge, and why.

```
$ python -m codeeval evaluate tasks --out reports

two_sum
  1. candidate_a      100.0  A  Accept
  2. candidate_b       85.1  B  Revise
  3. candidate_c       65.4  D  Reject
```

Every candidate gets a per-dimension score, a verdict, and reviewer-style notes such as
``[robustness] `test_edge_same_element_not_reused` failed — assertion failed: `assert two_sum([5, 1], 10) is None` ``
and ``[maintainability] L7 E001: bare `except:` also catches KeyboardInterrupt/SystemExit``.

## What it measures

| Dimension        | Weight | Signal                                                                  |
| ---------------- | -----: | ----------------------------------------------------------------------- |
| Correctness      |   0.45 | share of **core** tests passed                                          |
| Robustness       |   0.20 | share of **edge-case** tests passed (`test_edge_*`)                     |
| Efficiency       |   0.15 | **performance** tests (`test_perf_*`) + runtime vs. fastest correct run |
| Maintainability  |   0.20 | static analysis: complexity, nesting, smells, unused imports, …         |

Verdict: **Accept** (all core + perf tests pass, ≥ 80 % of edge tests, no error-level
findings), **Revise** (≥ 60 % core), otherwise **Reject**. Weights are configurable.

An optional **LLM judge** (`--llm-judge`) adds a second opinion. It is shown the
*actual test outcomes* so it cannot hallucinate correctness, and its score is blended
into the overall with a configurable weight. The judge is vendor-agnostic: it takes any
`complete(prompt) -> str` callable (an Anthropic Messages API implementation is included).

## How it works

```
tasks/<name>/
├── task.md            # problem statement shown to the model and to the judge
├── tests.py           # hidden tests: test_*, test_edge_*, test_perf_*
└── candidates/*.py    # solutions to evaluate (e.g. from different models/prompts)
```

1. **Run** — each candidate is executed in a fresh `python -I` subprocess in a temp
   directory, with a per-test timeout (`SIGALRM`), a whole-run timeout and an
   address-space limit. Failures, errors and timeouts are distinguished.
2. **Analyse** — the source is parsed with `ast`; per-function McCabe complexity,
   nesting depth, length and parameter count are computed, and twelve common smells
   are flagged (bare `except`, swallowed exceptions, mutable defaults, `eval`, …).
   `ruff` is used as an extra signal when installed.
3. **Score** — the rubric combines the two into four dimensions, an overall score and
   a verdict.
4. **Report** — `reports/report.md` for humans, `reports/report.json` for pipelines.

The runner isolates candidates, but it is *not* a security sandbox — use a container
for untrusted code.

## Bundled tasks

Four tasks with three candidates each, written to mirror the mistakes models actually
make:

| Task              | `candidate_a`       | `candidate_b`                                   | `candidate_c`                                        |
| ----------------- | ------------------- | ----------------------------------------------- | ---------------------------------------------------- |
| `two_sum`         | hash map, O(n)      | brute force — correct but times out on 10⁵      | reuses the same element; wrong pair ordering         |
| `lru_cache`       | `OrderedDict`       | list-based recency — O(n) ops, too slow         | `get` doesn't refresh recency; bare `except`         |
| `parse_log_line`  | anchored regex      | `str.split` — breaks on quoted fields w/ spaces | returns `None` instead of raising; mutable default   |
| `merge_intervals` | sort + sweep        | mutates input; misses touching intervals        | correct but O(n²) repeated-merge loop                |

Run `python -m codeeval evaluate tasks` to see the full report (an example is in
[`examples/sample_report.md`](examples/sample_report.md)).

## Install & use

```bash
git clone https://github.com/Priyal2004784/ai-code-eval-harness
cd ai-code-eval-harness
pip install -e ".[dev]"        # no runtime dependencies; dev adds pytest + ruff

pytest                          # 35 tests for the harness itself
python -m codeeval list tasks
python -m codeeval evaluate tasks --out reports
python -m codeeval evaluate tasks --task two_sum --timeout 2 --weights 0.5,0.2,0.1,0.2
ANTHROPIC_API_KEY=... python -m codeeval evaluate tasks --llm-judge
```

Add your own task by creating a folder with `task.md`, `tests.py` and `candidates/`.
Tests are plain functions that import the candidate as `solution`; no pytest needed
inside the sandbox.

## Why I built this

I wanted a repeatable way to answer "is this AI-generated solution good enough to
merge?" that goes beyond "the tests pass". Reviewing model output well means checking
edge cases, asymptotic behaviour and code hygiene — the same things a senior engineer
looks for — and writing that feedback down in a form that is useful to both humans and
models.

## Layout

```
codeeval/
├── runner.py     # sandboxed execution, per-test timeouts, result model
├── static.py     # ast-based complexity + smell detection
├── rubric.py     # weights, scoring, grades, verdicts
├── feedback.py   # reviewer-style remarks
├── judge.py      # optional LLM judge (vendor-agnostic)
├── evaluate.py   # task discovery + pipeline
├── report.py     # Markdown / JSON output
└── cli.py
```

MIT licensed.
