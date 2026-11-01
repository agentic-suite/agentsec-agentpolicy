# Policy Backtest & PR Decision-Diff — Design (M20, v0.1.0)

**BLUF:** M20 replays a window of recorded agentwatch history against a **candidate** policy versus the
**baseline** in force and emits the exact **flip set** — newly-denied / newly-asked / newly-allowed /
unchanged — attachable to a policy PR. It is **read-only** (no re-execution, no fleet events) and **advisory**
(watermarked `backtest`, excluded from live analytics and the golden gate). This is the design of record
(`20.D0`); it delivers **CUJ-29** (R43).

> Status: **Done** — branch `feat-0.1.0`. Module: `agentpolicy/backtest.py`, `cli/backtest.py`.

---

## 1. The backtest engine (`20.1`)

`agentpolicy/backtest.py`:

* `load_history(path)` — read a JSONL window of `agentwatch.security_event.v1` (`policy.decision`) events.
* `call_from_event(event)` — reconstruct the canonical `NormalizedCall` from an event's
  `principal` / `action` / `resource` blocks (the same shape the engine emitted).
* `backtest(events, candidate, *, baseline=None, emit=None) -> BacktestReport` — replay each event through the
  **baseline** engine and the **candidate** engine, classify each call into one of three outcomes
  (`deny` / `ask` = escalate / `allow`), and bucket the transition:
  * same outcome → **unchanged**;
  * candidate `deny` → **newly-denied**;
  * candidate `ask` → **newly-asked**;
  * otherwise → **newly-allowed**.

The **flip set is exact and reproducible**: events are replayed in input order with `(event_id)` as the stable
tiebreaker, and the classification is a pure function of the two decisions — the same history + policies always
produce the same report.

## 2. Read-only & advisory (`20.3`)

Backtest **re-executes nothing** in the live path: it evaluates reconstructed calls through a throwaway engine
and **emits no fleet events** (`emit` is a hook that the backtest never calls — a spy proves it). The report is
**watermarked `backtest`** and **advisory** — it is excluded from live analytics and from the CI golden gate, so
a flip is a **review signal, never a build failure**. Every report also states its **coverage window**
(`window_start`/`window_end` from the events) and its **limits** (history ≠ future; the window is a sample, not
a proof).

## 3. PR decision-diff (`20.2`)

`agentpolicy backtest --history <window> --candidate <policy> [--baseline <policy>] [--ci]`:

* evaluates the window and prints (or `--json` dumps) the flip set with the reasons and each action's context;
* `--ci` attaches a compact **step summary** to `$GITHUB_STEP_SUMMARY` (the PR check summary) and always exits
  **0** — the diff informs review, it never auto-blocks the PR.

## 4. WBS M20 item mapping

| Item | Where |
|---|---|
| 20.D0 design docs first | this document |
| 20.1 backtest engine | `agentpolicy/backtest.py` |
| 20.2 PR decision-diff (`--ci`) | `cli/backtest.py` |
| 20.3 advisory + watermark | `BacktestReport.watermark`, `advisory`, window + limits |
| 20.T/20.C/20.L/20.CR/20.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [backtest reference](../reference/backtest-and-pr-diff.md) |
