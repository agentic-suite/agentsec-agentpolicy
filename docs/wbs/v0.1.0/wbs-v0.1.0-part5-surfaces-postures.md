# WBS v0.1.0 — Part 5: Delivery Surfaces & Postures (M8–M9)

**BLUF:** M8 exposes the PDP through **every delivery surface** — library, CLI, MCP server, HTTP — plus the
adapter registry (CUJ-2). M9 ships **posture presets, `init`, `diff` and lint** and the policy-export surface for
policyweave (CUJ-8, CUJ-16, CUJ-17).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M8 — Delivery surfaces & adapters

**Goal:** one decision engine, several surfaces (library, CLI, MCP server, HTTP), with a validated adapter
registry for harnesses/frameworks.

**CUJ:** **CUJ-2** · **Requirements:** R28.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 8.D0 | **Design docs first** | Surface contract (one engine, N bindings) + adapter-registry design | docs | reviewed before code | #96 | — | — |
| 8.1 | Library surface | In-process `evaluate(...)` (the 15-line path) | library | same decision as every surface | #97 | CUJ-2 | R28 |
| 8.2 | MCP server surface | Read-only `evaluate`/`explain` as MCP tools | MCP server | an MCP client gets a decision | #98 | CUJ-2 | R28 |
| 8.3 | HTTP surface | Local HTTP PDP (the base for the M14 AuthZEN binding) | HTTP | a non-Python caller gets a decision | #99 | CUJ-2 | R28 |
| 8.4 | Adapter registry | Harness hooks, MCP client wrapper, LangGraph/PydanticAI/OpenAI-SDK adapters; validated at load | registry | unknown adapter → `ConfigError` | #100 | CUJ-2 | R28 |
| 8.5 | Wire into an enforcer | Reference integration (a harness hook + the MCP-proxy path) | integration | a denied call returns a replan-able rejection | #101 | CUJ-2 | R28 |
| 8.T | Tests | Same decision across surfaces; adapter conformance; deny is model-consumable | tests | coverage ≥ 95% | #102 | CUJ-2 | R28 |
| 8.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #103 | — | — |
| 8.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #104 | — | — |
| 8.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #105 | — | — |
| 8.D | Docs | Surface reference + adapter guide + harness-compatibility table (PRD 19) | docs | updated + linked | #106 | — | — |
| 8.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 8.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A non-Python caller and an in-process caller get the same decision (R28)
- [ ] Wiring into a harness/enforcer works; a denied call is model-consumable (**CUJ-2**)

---

## Milestone M9 — Posture presets, init, diff & lint

**Goal:** never a blank slate — three **posture presets** with an `init` scaffold, a policy `diff`, **lint**
(unused/shadowed/over-permissive/cross-pack/secrets-in-policy), and the policy-export surface for policyweave.

**CUJ:** **CUJ-8**, **CUJ-16**, **CUJ-17** · **Requirements:** R12, R16.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 9.D0 | **Design docs first** | Posture-presets design + lint design + policy-export (policyweave) design | docs | reviewed before code | #107 | — | — |
| 9.1 | Posture presets | `strict`/`balanced`/`permissive` as commented, pre-populated Cedar policies | presets | `init --posture` emits a populated policy | #108 | CUJ-8 | R16 |
| 9.2 | `init` scaffold | Generate policy + adapter + quickstart; never blank | CLI | commenting/scaffold present | #109 | CUJ-8 | R16 |
| 9.3 | `agentpolicy diff` | Kept vs overridden vs gaps | CLI | diff is one command | #110 | CUJ-8 | R16 |
| 9.4 | Rule-pack lint | Unused/shadowed/over-permissive + cross-pack outcome-conflict + literal-secrets-in-policy | lint | findings with locations; CI-failable | #111 | CUJ-17 | R12 |
| 9.5 | Policy export (policyweave) | Emit the Cedar source + compiled artifacts for policyweave targets | export | one policy → harness formats | #112 | CUJ-16 | R16 |
| 9.T | Tests | Posture behavior matrix, init/diff, lint findings, export | tests | coverage ≥ 95% | #113 | CUJ-8, CUJ-17 | R12, R16 |
| 9.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #114 | — | — |
| 9.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #115 | — | — |
| 9.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #116 | — | — |
| 9.D | Docs | Posture/init reference + lint reference + policyweave export note | docs | updated + linked | #117 | — | — |
| 9.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 9.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A posture preset yields a working policy; overrides don't allow a dangerous action (**CUJ-8**)
- [ ] Lint reports unused/shadowed/over-permissive/conflict/secrets findings (**CUJ-17**)
- [ ] One policy compiles outward for the harness (policyweave handoff) (**CUJ-16**)

---

Part 5 green ⇒ the PDP is callable from anywhere and configurable without a blank slate; proceed to
[Part 6 (M10–M11)](wbs-v0.1.0-part6-shadow-ci.md).
