# WBS v0.1.0 — Part 6: Shadow Mode & CI Gate (M10–M11)

**BLUF:** M10 ships **shadow mode + calibration + canary rollout** — trust before you enforce (CUJ-4). M11 ships
the **CI regression suite** (goldens + agentdrill replays), the **fail-closed fuzz coverage** of every path
(CUJ-9), and the **compliance evidence export** (CUJ-7).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M10 — Shadow mode, calibration & canary

**Goal:** deploy in observe-only first, tune, then flip — with a calibration report (false-block/miss rates) and
a canary rollout between shadow and full enforce.

**CUJ:** **CUJ-4** · **Requirements:** R30.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 10.D0 | **Design docs first** | Shadow/calibration/canary design: `dry_run`, counterfactual thresholds, rollout % | docs | reviewed before code | #118 | — | — |
| 10.1 | Shadow mode | `dry_run` returns the decision, logs it, returns `allow` to the caller | engine | shadow decisions logged, invisible to the agent | #119 | CUJ-4 | R30 |
| 10.2 | `audit query --dry-run` | Show what *would have* been blocked/escalated; one diff | CLI | shadow→enforced diff is one filter | #120 | CUJ-4 | R30 |
| 10.3 | Calibration report | False-block/miss rates + counterfactual thresholds | report | rates reported | #121 | CUJ-4 | R30 |
| 10.4 | Canary rollout | Enforce on a configurable session percentage (5%→50%→100%) | engine | rollout is a knob | #122 | CUJ-4 | R30 |
| 10.T | Tests | Shadow invisibility, calibration math, canary selection determinism | tests | coverage ≥ 95% | #123 | CUJ-4 | R30 |
| 10.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #124 | — | — |
| 10.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #125 | — | — |
| 10.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #126 | — | — |
| 10.D | Docs | Shadow/calibration/canary reference | docs | updated + linked | #127 | — | — |
| 10.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 10.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Shadow logs decisions, agent never sees them; the flip is one filter (**CUJ-4**)
- [ ] Calibration rates + canary rollout present

---

## Milestone M11 — CI regression suite & fail-closed hardening

**Goal:** golden decision fixtures gate every policy PR, an agentdrill replay rejects an un-blocking change, and
every failure path is proven fail-closed. Closes the **v0.1.0 core** (a leaner release may ship after M11).

**CUJ:** **CUJ-7**, **CUJ-9** · **Requirements:** R22, R8, R32 (partial).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 11.D0 | **Design docs first** | CI-gate design + fail-closed matrix + coverage-export design | docs | reviewed before code | #128 | — | — |
| 11.1 | Golden regression suite | Golden decision fixtures replayed per PR; deterministic drift detection | suite | a golden deny→allow flip fails the build | #129 | CUJ-7 | R22 |
| 11.2 | agentdrill replay gate | A change that un-blocks a named incident replay is rejected | CI job | the replay gate blocks the PR | #130 | CUJ-7 | R22 |
| 11.3 | Fail-closed fuzz | Fuzz the input space; assert every failure path denies with a distinct reason | fuzz suite | 0 failure modes silently allow | #131 | CUJ-9 | R8 |
| 11.4 | Coverage/evidence export | Export the standards coverage matrix (OWASP ASI/LLM, ATLAS) for agentcomply | export | matrix regenerated in CI | #132 | — | R32 |
| 11.T | Tests | Golden gate, replay gate, fail-closed paths, export | tests | coverage ≥ 95% | #133 | CUJ-7, CUJ-9 | R22, R8 |
| 11.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #134 | — | — |
| 11.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #135 | — | — |
| 11.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #136 | — | — |
| 11.D | Docs | CI-gate reference + fail-closed matrix + success-metrics wiring | docs | updated + linked | #137 | — | — |
| 11.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 11.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A golden deny→allow flip fails the build; an un-blocking change is rejected (**CUJ-7**)
- [ ] No failure mode silently allows (fuzzed) (**CUJ-9**); coverage matrix exported

> **v0.1.0 core complete after M11.** M12–M23 are the P1/P2 additions (a leaner release may tag here); M24–M25
> close any release.

---

Part 6 green ⇒ the v0.1.0 core is regression-gated and fail-closed; proceed to
[Part 7 (M12–M13)](wbs-v0.1.0-part7-budgets-exfil.md).
