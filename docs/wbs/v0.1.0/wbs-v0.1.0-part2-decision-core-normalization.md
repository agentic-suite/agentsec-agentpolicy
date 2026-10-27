# WBS v0.1.0 — Part 2: Cedar Decision Core & Normalization (M2–M3)

**BLUF:** M2 builds the **Cedar decision core** — the five outcomes, the evaluator, the decision shaper, and the
mandatory human-gate class (this is the milestone that delivers **CUJ-1**). M3 builds the **canonical action
model** — normalization, the taxonomy, the contextual matrix, and dispatcher-bypass safety.

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M2 — Cedar decision core (five outcomes)

**Goal:** evaluate a Cedar policy against a canonical action and return one of **five outcomes** with the
mandatory human-gate class, deterministically, in the inline latency budget.

**CUJ:** **CUJ-1** · **Requirements:** R1, R2 (Cedar), R4, R8.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 2.D0 | **Design docs first** | Decision-core design: the five-outcome semantics, decision shaper, gate class, latency budget | docs | reviewed before code | #30 | — | — |
| 2.1 | Cedar evaluator | Deterministic Cedar evaluation over the canonical action; no ML/network in path | engine | same input+policy ⇒ same decision | #31 | CUJ-1 | R2 |
| 2.2 | Five-outcome decision shaper | Map Cedar result + pack metadata → `allow`/`deny`/`ask`/`rate-limit`/`redact` with criticality | shaper | all five outcomes in the acceptance matrix | #32 | CUJ-1 | R1 |
| 2.3 | Mandatory human-gate class | Irreversible actions default to `ask`; changing the default is a logged amendment | policy module | gate class enforced; amendment logged | #33 | CUJ-1 | R4 |
| 2.4 | Decision model | `Decision`/`Factor`/`Explanation` dataclasses + JSON shape (PRD 15) | models | model matches PRD 15 | #34 | CUJ-1 | R1 |
| 2.5 | Latency budget | Sub-100 ms p99 measured locally; cold-start budget | benchmark | p99 < 100 ms in CI | #35 | CUJ-1 | R8 |
| 2.T | Tests | The acceptance matrix (tool × env × action × data-class); five-outcome correctness | tests | coverage ≥ 95% | #36 | CUJ-1 | R1 |
| 2.C | Coverage gate | coverage ≥ 95% on this milestone's modules | report | ≥ 95% | #37 | — | — |
| 2.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #38 | — | — |
| 2.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #39 | — | — |
| 2.D | Docs | Decision-core design + reference (outcomes, criticality, reason codes seed) | docs | updated + linked | #40 | — | — |
| 2.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 2.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] All five outcomes demonstrable in automated tests (**CUJ-1**)
- [ ] Sub-100 ms p99 measured; gate class enforced

---

## Milestone M3 — Action normalization, taxonomy & contextual model

**Goal:** convert any incoming call into one **canonical action**, drive decisions from the contextual model
(tool category, action class, environment, data sensitivity, agent class), and close dispatcher/obfuscation
bypasses.

**CUJ:** — (enables CUJ-1, CUJ-11) · **Requirements:** R15, R24 (closes predecessor G-1/G-2 as P0).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 3.D0 | **Design docs first** | Normalization spec, canonical action shape, taxonomy + contextual-dimension design | docs | reviewed before code | #41 | — | — |
| 3.1 | Canonical action normalizer | MCP `tools/call`, LangGraph tool node, raw Python, HTTP, dispatcher → canonical `(principal, action, resource, context)` | normalizer | one shape for both normalizer and evaluator | #42 | — | R15 |
| 3.2 | Tool-name normalization | Case/whitespace/Unicode folding before matching; unknown normalized name → deny | normalizer | obfuscated name denied (`unknown_action`) | #43 | — | R24 |
| 3.3 | Dispatcher-bypass safety | Parse coarse input (`bash: "git push --force"`) to canonical `(tool, action)` and evaluate the same policy | normalizer | smuggled action denied | #44 | — | R24 |
| 3.4 | Action taxonomy (13 domains) | Ship the domain→verb→baseline-risk taxonomy as a policy module | policy module | every verb normalizes to a domain | #45 | — | R15 |
| 3.5 | Contextual model | Decide from the five dimensions + session context; matrix test across env/data-class | engine | the same call scores differently across contexts | #46 | — | R15 |
| 3.T | Tests | Normalization (obfuscation/Unicode/dispatcher), taxonomy mapping, contextual matrix | tests | coverage ≥ 95% | #47 | — | R15, R24 |
| 3.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #48 | — | — |
| 3.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #49 | — | — |
| 3.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #50 | — | — |
| 3.D | Docs | Normalization spec + taxonomy reference | docs | updated + linked | #51 | — | — |
| 3.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 3.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Obfuscated/smuggled actions normalize to canonical and evaluate against the same policy (predecessor
      dispatcher/obfuscation gaps closed as P0)
- [ ] The contextual matrix scores the same call differently across environments/data classes

---

Part 2 green ⇒ the PDP decides all five outcomes over a canonical action; proceed to
[Part 3 (M4–M5)](wbs-v0.1.0-part3-packs-explain.md).
