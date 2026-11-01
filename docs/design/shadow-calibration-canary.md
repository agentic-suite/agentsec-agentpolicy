# Shadow Mode, Calibration & Canary — Design (M10, v0.1.0)

**BLUF:** M10 is **trust before you enforce**: deploy in observe-only first (`dry_run`), read a **calibration
report** (false-block / false-miss rates + counterfactual thresholds), then **flip** gradually with a
**deterministic canary** (enforce for a configurable session percentage). Shadow decisions are logged but
invisible to the agent, so nothing is blocked until the operator chooses to enforce. This is the design of record
(`10.D0`); it delivers **CUJ-4** (R30).

> Status: **Done** — branch `feat-0.1.0`. Modules: `engine/engine.py` (`dry_run` + canary), `canary.py`,
> `calibration.py`, `cli/{audit,calibrate}.py`.

---

## 1. Shadow mode (`10.1`)

`Engine(dry_run=True)` records the **real** decision in the audit trail and returns `allow` to the caller; the
returned decision carries `dry_run=True` and a `[DRY RUN] would have been <outcome>` explanation. Every path
(pre-score denies, obligation failures, scoping denies) funnels through `Engine._finalize`, so shadow is applied
uniformly and the audit trail always holds the *un-shadowed* verdict.

**Invisible to the agent:** the caller only ever sees `allow`; the real decision is available to operators via
the audit trail.

## 2. Inspect the shadow set (`10.2`)

`agentpolicy audit query --dry-run` filters the trail to shadow decisions — the *would-have-blocked /
would-have-escalated* set — so the shadow→enforced diff is one filter.

## 3. Calibration report (`10.3`)

`agentpolicy/calibration.py` — `calibrate(entries) -> CalibrationReport`. Over the shadow decisions it reports:

| Field | Definition |
|---|---|
| `shadow` | entries with `dry_run` set |
| `would_block` | shadow decisions in `deny`/`escalate` |
| `false_block` / `false_block_rate` | blocked decisions whose governing counterfactual boundary is ≤ 0.5 (near the allow boundary) |
| `allowed` | shadow decisions in `allow`/`audit`/`allow_with_obligation` |
| `false_miss` / `false_miss_rate` | allows whose counterfactual boundary is ≥ 0.75 (near the block boundary) |
| `threshold_table` | the counterfactual-threshold distribution |

**No ground truth ⇒ an explicit heuristic.** The boundaries (0.5 / 0.75) are parameters, documented in the
module and emitted in the report; a block that only just crossed the line is a *candidate* false block, not a
proven one. The raw threshold table is included so the operator can reason about the rates instead of trusting a
single number.

## 4. Canary rollout (`10.4`)

`agentpolicy/canary.py`:

* `canary_selected(session_id, percent)` — the cohort is a **stable hash**: `int(sha256(session_id)[:8], 16) % 100
  < percent`. The same session id lands in the same bucket on every run and machine, so a session never flickers
  between enforced and shadowed and a rollout is reproducible.
* `CanaryConfig(percent).enforces(session_id)` — `0` disables the canary (full enforce, the historical
  behaviour); `100` enforces for everyone; a **missing** session id is not selected until `100` (safe default).
* `STAGES = (5, 50, 100)` — the conventional rollout ladder.

**Engine integration.** `Engine(canary_percent=N)` folds the canary into `_finalize` next to `dry_run`:
`shadow = dry_run or (canary on and session not selected)`. The audit record marks a canary-shadowed decision
`dry_run=True`, so the calibration report and `audit query --dry-run` cover canary decisions too.

## 5. Fail-closed / determinism

* Determinism: the canary bucket and the calibration rates are pure functions of their inputs (no clock, no
  network).
* Safety: shadow and canary both **default to not blocking** only when explicitly configured; `dry_run=True`
  always wins; a malformed percentage raises.

## 6. WBS M10 item mapping

| Item | Where |
|---|---|
| 10.D0 design docs first | this document |
| 10.1 shadow mode | `engine/engine.py` (`_finalize`) |
| 10.2 `audit query --dry-run` | `cli/audit.py` |
| 10.3 calibration report | `agentpolicy/calibration.py`, `cli/calibrate.py` |
| 10.4 canary rollout | `agentpolicy/canary.py`, `engine/engine.py` |
| 10.T/10.C/10.L/10.CR/10.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [shadow/calibration reference](../reference/shadow-calibration-canary.md) |
