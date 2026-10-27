# WBS v0.1.0 — Part 7: Budgets, Rate Limits & Exfil-Sink (M12–M13)

**BLUF:** M12 ships **session state, blast-radius budgets and rate/burst limits** (CUJ-12, CUJ-18). M13 ships the
**exfil-sink rule class, argument-level validation and discovery-time tool hiding** (CUJ-13).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M12 — Session state, blast-radius budgets & rate limits

**Goal:** cumulative, per-session capability ceilings (*10 files, 20 requests, $5 — then stop*) and rate/burst
limits, with a `retry_after` the agent can honor. The novel class nobody else ships.

**CUJ:** **CUJ-12**, **CUJ-18** · **Requirements:** R9, R17, R23.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 12.D0 | **Design docs first** | Session-state + budget semantics design (cumulative, reset/inherit) + rate-limit design | docs | reviewed before code | #138 | — | — |
| 12.1 | Session/context state | Cumulative counters + consent scope; replayable by `session_id` | store | state reconstructs for review | #139 | CUJ-12 | R17 |
| 12.2 | Blast-radius budgets | Capability ceilings (files/requests/spend/calls); budget state in every decision | engine | exhaustion → `rate-limit`/halt with a reason | #140 | CUJ-12 | R9 |
| 12.3 | Rate/burst limits | Per-session op-count + burst ceilings + **`retry_after`** | engine | a runaway loop is throttled | #141 | CUJ-18 | R23 |
| 12.4 | agenthalt integration | Hard-exhaustion triggers a halt (freeze + evidence) | integration | halt trigger fires | #142 | CUJ-12 | R9 |
| 12.T | Tests | Cumulative counting (no split evasion), budget exhaustion, retry_after, halt trigger | tests | coverage ≥ 95% | #143 | CUJ-12, CUJ-18 | R9, R23 |
| 12.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #144 | — | — |
| 12.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #145 | — | — |
| 12.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #146 | — | — |
| 12.D | Docs | Budget reference + session-state reference + budget pack | docs | updated + linked | #147 | — | — |
| 12.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 12.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Exhaustion returns `rate-limit`/halt with a reason; splitting does not evade (**CUJ-12**)
- [ ] A runaway loop is throttled with a `retry_after` (**CUJ-18**)

---

## Milestone M13 — Exfil-sink, argument validation & tool hiding

**Goal:** block outputs carrying secrets/PII from reaching external-sink tools (taint-lite, no ML), validate
arguments semantically, and hide tools an agent can't call.

**CUJ:** **CUJ-13** · **Requirements:** R10, R19, R21.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 13.D0 | **Design docs first** | Exfil-sink rule design + argument-validator design + tool-hiding design | docs | reviewed before code | #148 | — | — |
| 13.1 | Exfil-sink rule class | Block outputs carrying secrets/PII flowing to external-sink tools; name source + sink | pack | blocks the documented exfil chain | #149 | CUJ-13 | R10 |
| 13.2 | Argument-level validation | regex/range/enum/path-containment/URL-allowlist validators | validators | SELECT-only, refund cap, SSRF, path containment | #150 | — | R19 |
| 13.3 | Discovery-time tool hiding | Don't expose tools the policy would deny | engine | an agent never sees a denied tool | #151 | — | R21 |
| 13.T | Tests | Exfil chain blocked, validators, tool-hiding surface | tests | coverage ≥ 95% | #152 | CUJ-13 | R10, R19, R21 |
| 13.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #153 | — | — |
| 13.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #154 | — | — |
| 13.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #155 | — | — |
| 13.D | Docs | Exfil-sink reference + validator reference + tool-hiding note | docs | updated + linked | #156 | — | — |
| 13.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 13.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] The exfil chain is blocked and names source + sink (**CUJ-13**, R10)
- [ ] Argument validators + tool hiding enforced

---

Part 7 green ⇒ volume and data-flow are policy concerns; proceed to
[Part 8 (M14–M15)](wbs-v0.1.0-part8-stepup-freeze.md).
