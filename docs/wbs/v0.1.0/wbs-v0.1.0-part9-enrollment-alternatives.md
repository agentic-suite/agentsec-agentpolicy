# WBS v0.1.0 — Part 9: Enrollment, Analytics & Multi-Agent (M16–M17)

**BLUF:** M16 ships **agent enrollment/probation and approval analytics** — the safe first-seen posture and the
rubber-stamp detector (CUJ-22, CUJ-23). M17 ships **nearest-permissible-action and multi-agent governance** —
denials that replan, and delegation-scope proofs (CUJ-24, CUJ-28).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M16 — Enrollment/probation & approval analytics

**Goal:** a first-seen unknown agent lands in a **probation** posture (read + audit + ask-on-write) until a human
classifies it; and the **approval-analytics** report surfaces rubber-stamp gates.

**CUJ:** **CUJ-22**, **CUJ-23** · **Requirements:** R35, R36.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 16.D0 | **Design docs first** | Enrollment-ledger + probation-posture design; approval-analytics design | docs | reviewed before code | #176 | — | — |
| 16.1 | Enrollment ledger + probation | First-seen unknown agent → probation posture; classification is a logged event | engine | first write → `ask` + `agent_probation` | #177 | CUJ-22 | R35 |
| 16.2 | `enrollment-probation` pack | Shipped probation posture pack | pack | probation enforces read + ask-on-write | #178 | CUJ-22 | R35 |
| 16.3 | Approval analytics | `agentpolicy report approvals`: approval rate, latency, shadow→enforce delta, rubber-stamp gates | report | an always-approved gate is flagged | #179 | CUJ-23 | R36 |
| 16.4 | agentwatch inventory link | Classification feeds the fleet inventory (no shadow IdP) | integration | classification event visible | #180 | CUJ-22 | R35 |
| 16.T | Tests | Probation flow, classification event, rubber-stamp detection on a corpus | tests | coverage ≥ 95% | #181 | CUJ-22, CUJ-23 | R35, R36 |
| 16.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #182 | — | — |
| 16.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #183 | — | — |
| 16.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #184 | — | — |
| 16.D | Docs | Enrollment/probation reference + approval-analytics reference | docs | updated + linked | #185 | — | — |
| 16.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 16.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] An unknown agent's first write → `ask` + `agent_probation`; classification logged (**CUJ-22**)
- [ ] The analytics report flags a synthetic always-approved gate (**CUJ-23**)

---

## Milestone M17 — Nearest-permissible-action & multi-agent governance

**Goal:** every deny/ask carries **verified-permissible alternatives** the agent can replan to; delegation chains
are scope-subset-proven; inter-agent requests are decided like any action.

**CUJ:** **CUJ-24**, **CUJ-28** · **Requirements:** R37, R39, R25.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 17.D0 | **Design docs first** | Alternative-generation design (agent/operator split) + multi-agent governance design | docs | reviewed before code | #186 | — | — |
| 17.1 | `permitted_alternatives[]` | Verified-permissible variants; agent-facing template, no policy internals | engine | alternatives are evaluated-true | #187 | CUJ-24 | R37 |
| 17.2 | Delegation-chain + scope-subset | `delegation_chain` in principal; child ⊆ parent, proven | engine | out-of-scope child denied, link named | #188 | CUJ-28 | R39 |
| 17.3 | Inter-agent decisions | An agent→agent request evaluates through the same engine | engine | decided like any action | #189 | CUJ-28 | R39 |
| 17.4 | `multi-agent-delegation` pack | Shipped delegation/scope rules | pack | scope-subset enforced | #190 | CUJ-28 | R39 |
| 17.T | Tests | Alternatives verified-permissible + no-leak; chain subset proof; inter-agent decide | tests | coverage ≥ 95% | #191 | CUJ-24, CUJ-28 | R37, R39 |
| 17.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #192 | — | — |
| 17.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #193 | — | — |
| 17.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #194 | — | — |
| 17.D | Docs | Alternatives reference + multi-agent governance reference | docs | updated + linked | #195 | — | — |
| 17.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 17.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A denied call returns a verified-permissible alternative; no policy internals leak (**CUJ-24**)
- [ ] A child's out-of-parent-scope action is denied naming the chain link (**CUJ-28**)

---

Part 9 green ⇒ first-seen agents are safe and denials replan; proceed to
[Part 10 (M18–M19)](wbs-v0.1.0-part10-breakglass-drafting.md).
