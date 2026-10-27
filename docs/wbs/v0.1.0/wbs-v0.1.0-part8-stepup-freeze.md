# WBS v0.1.0 — Part 8: Step-up, AuthZEN & Freeze Windows (M14–M15)

**BLUF:** M14 ships **scope-escalation/step-up, the AuthZEN Authorization API 1.0 interop binding, and the
adversarial resilience suite** (CUJ-11, CUJ-14, CUJ-19). M15 ships **change-freeze windows and data-class
derivation** (CUJ-21).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M14 — Step-up, AuthZEN interop & adversarial suite

**Goal:** react to authorization-challenge events with narrower-scope step-up, expose a conformant **AuthZEN**
PDP surface, and prove the engine cannot be tricked.

**CUJ:** **CUJ-11**, **CUJ-14**, **CUJ-19** · **Requirements:** R11, R26, R27.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 14.D0 | **Design docs first** | Step-up design + AuthZEN binding design + adversarial-suite design | docs | reviewed before code | #157 | — | — |
| 14.1 | Scope-escalation/step-up | React to a 403 challenge with a narrower-scope request (AuthZEN step-up `acr_values`) | engine | the loop is least-privilege | #158 | CUJ-19 | R11 |
| 14.2 | AuthZEN Authorization API 1.0 | `POST /access/v1/evaluation` (+ boxcarring, decision context); conformant | HTTP | a conformant AuthZEN caller gets the same decision | #159 | CUJ-14 | R27 |
| 14.3 | MCP-server ask path | Ask the gate from an MCP client (non-Python host) | MCP server | same decision as in-process | #160 | CUJ-14 | R27 |
| 14.4 | Adversarial resilience suite | Injection/obfuscation/dispatcher/tamper/replay/flood; every attempt blocks + logs a distinct reason | suite | the adversarial sub-matrix passes | #161 | CUJ-11 | R26 |
| 14.T | Tests | Step-up loop, AuthZEN conformance, MCP path, adversarial sub-matrix | tests | coverage ≥ 95% | #162 | CUJ-11, CUJ-14, CUJ-19 | R11, R26, R27 |
| 14.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #163 | — | — |
| 14.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #164 | — | — |
| 14.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #165 | — | — |
| 14.D | Docs | AuthZEN conformance note + step-up reference + adversarial matrix | docs | updated + linked | #166 | — | — |
| 14.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 14.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] The engine resists every attempted bypass, each logged with a distinct reason (**CUJ-11**)
- [ ] A conformant AuthZEN caller + an MCP client get the same decision (**CUJ-14**)
- [ ] Step-up loop is least-privilege by construction (**CUJ-19**)

---

## Milestone M15 — Freeze windows & data-class derivation

**Goal:** express the Replit condition — a declared freeze that tightens posture for its window — and derive
`data_class` deterministically so adopters don't hand-tag everything.

**CUJ:** **CUJ-21** · **Requirements:** R33, R34.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 15.D0 | **Design docs first** | Freeze-window design (declaration, overlap, audit) + data-class derivation design | docs | reviewed before code | #167 | — | — |
| 15.1 | Freeze windows | A declared, audited freeze tightens posture for its window; `freeze_id` on decisions | engine + CLI | a freeze flips the posture; on/off audited | #168 | CUJ-21 | R33 |
| 15.2 | Freeze policy pack | `code-freeze` pack any policy can reference (context condition) | pack | write-in-prod → `ask`/`deny` during a freeze | #169 | CUJ-21 | R33 |
| 15.3 | Data-class derivation | Globs/tags/schema hints derive `data_class`, deterministically; conflict fails loudly | engine | an untagged resource resolves | #170 | — | R34 |
| 15.T | Tests | Freeze flips posture + audit; overlap strictest wins; data-class derivation + conflict | tests | coverage ≥ 95% | #171 | CUJ-21 | R33, R34 |
| 15.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #172 | — | — |
| 15.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #173 | — | — |
| 15.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #174 | — | — |
| 15.D | Docs | Freeze reference + data-class derivation reference | docs | updated + linked | #175 | — | — |
| 15.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 15.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A declared freeze tightens posture for its window and is audited on/off (**CUJ-21**)
- [ ] `data_class` resolves from derivation; a conflict fails loudly, never silently

---

Part 8 green ⇒ the PDP is interop-standard, bypass-resistant, and can express the exact Replit condition;
proceed to [Part 9 (M16–M17)](wbs-v0.1.0-part9-enrollment-alternatives.md).
