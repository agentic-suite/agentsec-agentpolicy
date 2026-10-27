# WBS v0.1.0 — Part 11: Backtest & Layering (M20–M21)

**BLUF:** M20 ships **policy backtest + PR decision-diff** — prove what a change would have done to real history
(CUJ-29). M21 ships **narrow-only policy layering and the action-space coverage report** — guarantee the floor
and expose the uncovered quadrant (CUJ-30, CUJ-31).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M20 — Policy backtest & PR decision-diff

**Goal:** replay a window of recorded agentwatch history against a candidate policy, emit the exact flip set
(newly-denied / newly-asked / newly-allowed / unchanged), and attach it to the policy PR — **read-only** and
**advisory**.

**CUJ:** **CUJ-29** · **Requirements:** R43.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 20.D0 | **Design docs first** | Backtest design: replay fidelity, watermarked `backtest`, coverage window, advisory-only (no golden-gate pollution) | docs | reviewed before code | #215 | — | — |
| 20.1 | Backtest engine | `agentpolicy backtest --history <window> --candidate <policy>`; read-only replay | engine | flip set exact + reproducible | #216 | CUJ-29 | R43 |
| 20.2 | PR decision-diff | `--ci` attaches the flip set to the step summary; no fleet events | CI | the diff is attached to the PR | #217 | CUJ-29 | R43 |
| 20.3 | Advisory + watermark | Watermarked `backtest`; excluded from live analytics and the golden gate; states window + limits | engine | a backtest flip is a review signal, never a failure | #218 | CUJ-29 | R43 |
| 20.T | Tests | Flip set exact over a fixture history; read-only; no fleet events; golden-gate exclusion | tests | coverage ≥ 95% | #219 | CUJ-29 | R43 |
| 20.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #220 | — | — |
| 20.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #221 | — | — |
| 20.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #222 | — | — |
| 20.D | Docs | Backtest reference + PR-diff reference | docs | updated + linked | #223 | — | — |
| 20.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 20.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] The flip set is exact and reproducible; the report states coverage + limits and is advisory (**CUJ-29**)
- [ ] Backtest emits no fleet events and never gates on its own flips

---

## Milestone M21 — Narrow-only layering & action-space coverage report

**Goal:** org baseline → project overlay → session consent where a child may only **restrict** (a widening overlay
fails at `check`); and a **coverage report** that names the exercised-but-uncovered verbs — `gap:unexplained` = 0.

**CUJ:** **CUJ-30**, **CUJ-31** · **Requirements:** R44, R45.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 21.D0 | **Design docs first** | Layering design (narrow-only invariant at load) + coverage-report design (four quadrants) | docs | reviewed before code | #224 | — | — |
| 21.1 | Layered composition | org → project → session; effective policy is the intersection | engine | composition loads deterministically | #225 | CUJ-30 | R44 |
| 21.2 | Narrow-only invariant | A widening overlay fails `agentpolicy check` at PR time, naming the rule | check | a widening overlay is rejected | #226 | CUJ-30 | R44 |
| 21.3 | Coverage report | `agentpolicy report coverage` — taxonomy × rules × fleet inventory; four quadrants | report | exercised-but-uncovered named loudly; `gap:unexplained` = 0 | #227 | CUJ-31 | R45 |
| 21.T | Tests | Widening overlay fails at check; floor holds under layer-combination fuzz; coverage quadrants | tests | coverage ≥ 95% | #228 | CUJ-30, CUJ-31 | R44, R45 |
| 21.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #229 | — | — |
| 21.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #230 | — | — |
| 21.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #231 | — | — |
| 21.D | Docs | Layering reference + coverage-report reference | docs | updated + linked | #232 | — | — |
| 21.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 21.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A widening overlay fails at `check`; no combination widens the floor (**CUJ-30**)
- [ ] The report names the exercised-but-uncovered quadrant; `gap:unexplained` = 0 (**CUJ-31**)

---

Part 11 green ⇒ policy changes are evidence-reviewed and fleets keep a floor; proceed to
[Part 12 (M22–M23)](wbs-v0.1.0-part12-selfattack-hardening.md).
