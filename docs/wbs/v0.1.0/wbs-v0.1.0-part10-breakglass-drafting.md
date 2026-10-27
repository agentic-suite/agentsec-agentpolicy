# WBS v0.1.0 — Part 10: Break-Glass, Dual-Control & NL Drafting (M18–M19)

**BLUF:** M18 ships **break-glass elevation with auto-revert and dual-control approvals** (CUJ-25, CUJ-26). M19
ships **NL policy drafting** — authoring-time, advisory only, locked out of the decision path (CUJ-27).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M18 — Break-glass & dual-control

**Goal:** a time-boxed, fully audited **break-glass** elevation that reverts automatically, and **dual-control**
(quorum) approvals for the irreversible class. Elevation never bypasses the human gate.

**CUJ:** **CUJ-25**, **CUJ-26** · **Requirements:** R40, R41.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 18.D0 | **Design docs first** | Break-glass design (reason, TTL, auto-revert, audit) + dual-control (quorum, distinct approver) design | docs | reviewed before code | #196 | — | — |
| 18.1 | Break-glass elevation | Time-boxed elevation with a logged reason; `break_glass_id` on decisions | engine + CLI | every decision in the window carries the id | #197 | CUJ-25 | R40 |
| 18.2 | Auto-revert | Reversion at expiry without manual action; revert is a logged event | engine | expiry reverts automatically | #198 | CUJ-25 | R40 |
| 18.3 | Dual-control approvals | Quorum (default 2) of distinct approvers for the irreversible class | engine | one approval ≠ release; two distinct = release | #199 | CUJ-26 | R41 |
| 18.4 | Composition guard | Break-glass widens scope ceilings only, never the human-gate class | engine | dual-control still applies inside a window | #200 | CUJ-25 | R40, R41 |
| 18.T | Tests | Expiry revert, break_glass_id propagation, quorum (same-principal rejected), composition | tests | coverage ≥ 95% | #201 | CUJ-25, CUJ-26 | R40, R41 |
| 18.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #202 | — | — |
| 18.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #203 | — | — |
| 18.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #204 | — | — |
| 18.D | Docs | Break-glass reference + dual-control reference | docs | updated + linked | #205 | — | — |
| 18.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 18.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Elevation expires and reverts without manual action, audited (**CUJ-25**)
- [ ] A single approval does not release a dual-control ask (**CUJ-26**)

---

## Milestone M19 — NL policy drafting

**Goal:** generate a candidate Cedar rule from a sentence, **advisory only** — it must compile, pass generated
tests + lint, and wait for human review. The runtime decision path is untouched (no ML).

**CUJ:** **CUJ-27** · **Requirements:** R42.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 19.D0 | **Design docs first** | NL-drafting design + the boundary lock (authoring-only; never a runtime path) | docs | reviewed before code | #206 | — | — |
| 19.1 | `agentpolicy draft` | Sentence → candidate Cedar rule via a model call **outside** runtime | CLI | a draft is produced | #207 | CUJ-27 | R42 |
| 19.2 | Generated tests | The draft emits `tests.yaml`; must compile + pass + lint | tooling | draft passes its tests or is rejected | #208 | CUJ-27 | R42 |
| 19.3 | Human-review gate + boundary lock | A draft is never auto-pinned; a test asserts no runtime path calls the model | tooling + test | runtime path untouched | #209 | CUJ-27 | R42 |
| 19.T | Tests | Draft compiles/passes; boundary lock; over-permissive draft caught by lint | tests | coverage ≥ 95% | #210 | CUJ-27 | R42 |
| 19.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #211 | — | — |
| 19.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #212 | — | — |
| 19.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #213 | — | — |
| 19.D | Docs | NL-drafting reference + explicit boundary note | docs | updated + linked | #214 | — | — |
| 19.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 19.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A one-sentence intent yields a candidate rule that compiles, passes its tests, and waits for review
      (**CUJ-27**)
- [ ] The decision path contains no ML (boundary-lock test)

---

Part 10 green ⇒ high-assurance governance and a lower authoring bar; proceed to
[Part 11 (M20–M21)](wbs-v0.1.0-part11-backtest-layering.md).
