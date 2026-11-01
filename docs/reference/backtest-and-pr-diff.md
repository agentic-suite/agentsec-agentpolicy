# Policy backtest & PR decision-diff — reference (v0.1.0)

WBS M20 · CUJ-29 · R43. Design: [policy-backtest-and-pr-diff.md](../design/policy-backtest-and-pr-diff.md).

Replay a window of recorded agentwatch history against a **candidate** policy and emit the exact **flip set**.
**Read-only** and **advisory** — it re-executes nothing live, emits no fleet events, and never fails a build.

```sh
agentpolicy backtest --history last-week.jsonl --candidate agentpolicy.yaml --ci
```

```python
from agentpolicy.backtest import backtest, load_history
from agentpolicy.policy.loader import load_policy

report = backtest(load_history("last-week.jsonl"), load_policy("candidate.yaml"))
report.newly_denied      # the exact flip set (each a Flip with before/after + reason)
report.watermark         # "backtest"
report.advisory          # True
report.coverage_note     # window + "% of fleet actions" style limits
```

The diff has four quadrants — **newly-denied** / **newly-asked** / **newly-allowed** / **unchanged** — and is
**exact and reproducible** (a pure function of the baseline/candidate decisions, replayed in a stable order).
`--ci` appends the summary to `$GITHUB_STEP_SUMMARY`; the command always exits **0** — a backtest flip is a
**review signal, not a golden-gate failure**.
