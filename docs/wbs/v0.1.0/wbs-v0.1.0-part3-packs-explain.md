# WBS v0.1.0 — Part 3: Rule Packs & Explain-Decision (M4–M5)

**BLUF:** M4 ships the **rule packs** — the pack format, the three launch packs (Replit rule, secret-in-output,
MCP allowlist), pack validate/test, and the OPA/Rego peer backend. M5 ships **explain-decision** — the reason
codes, the explanation/factor contract, and decisions emitted in the **agentwatch security-event schema**.

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M4 — Rule packs, pack tooling & policy backends

**Goal:** a versioned, incident-anchored **rule-pack** format with the three launch packs, `pack validate` /
`pack test`, and OPA/Rego as a peer backend.

**CUJ:** **CUJ-5** · **Requirements:** R2 (OPA import), R3, R29.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 4.D0 | **Design docs first** | Pack-format spec + pack-catalog design (metadata/rules/validators/tests; incident anchor) | docs | reviewed before code | #52 | — | — |
| 4.1 | Pack format + loader | `metadata.yaml` + `rules.cedar` + `validators.yaml` + `tests.yaml`; strict schema; path-safe ids | format | malformed pack → `ConfigError` | #53 | CUJ-5 | R29 |
| 4.2 | Launch pack — **destructive-commands (Replit rule)** | Destructive/irreversible action gate, incident-anchored | pack | blocks its named incident replay | #54 | CUJ-5 | R3 |
| 4.3 | Launch pack — **secret-in-output** | Block/scrub secrets+PII in tool output | pack | blocks the secret-exfil replay | #55 | CUJ-5 | R3 |
| 4.4 | Launch pack — **mcp-allowlist** | Default-deny unknown MCP servers/tools | pack | blocks the shadow-tool replay | #56 | CUJ-5 | R3 |
| 4.5 | `pack validate` / `pack test` | Validate schema + parse + run golden fixtures deterministically | CLI | `pack test` deterministic | #57 | CUJ-5 | R29 |
| 4.6 | OPA/Rego peer backend | Evaluate a Rego policy with the same decision contract; independent failure | backend | Rego unreachable ⇒ `opa_backend_unavailable` (deny) | #58 | — | R2 |
| 4.T | Tests | Pack schema/path-safety, each launch pack vs. its replay, `pack test`, Rego parity | tests | coverage ≥ 95% | #59 | CUJ-5 | R3 |
| 4.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #60 | — | — |
| 4.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #61 | — | — |
| 4.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #62 | — | — |
| 4.D | Docs | Pack-format spec, pack-catalog, schema | docs | updated + linked | #63 | — | — |
| 4.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 4.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Each launch pack demonstrates it blocks its named incident replay (**CUJ-5**, R3)
- [ ] Rego peer backend fails independently

---

## Milestone M5 — Explain-decision, reason codes & event schema

**Goal:** every decision is explainable — a machine `reason_code`, a human `explanation`, a `criticality`, the
`factors[]`, the matched rule — and every decision is emitted in the **agentwatch security-event schema**.

**CUJ:** **CUJ-3** · **Requirements:** R5, R6.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 5.D0 | **Design docs first** | Explain contract + reason-code registry + the agentwatch event binding design | docs | reviewed before code | #64 | — | — |
| 5.1 | Explain artifact | `matched_rule` + `factors[]` + `criticality` + `suggested_change` per decision | engine | every deny names a clause | #65 | CUJ-3 | R5 |
| 5.2 | Reason-code registry | Stable reason codes (policy_match, default_deny, unknown_action, irreversible_action, …) | registry | codes are stable + SIEM-alertable | #66 | CUJ-3 | R5 |
| 5.3 | Actionability | The one change that flips the outcome, plus the CI actionability test | engine + test | a human can name the change from the text alone | #67 | CUJ-3 | R5 |
| 5.4 | `agentpolicy explain` | CLI prints the full factor breakdown for an action | CLI | explain offline | #68 | CUJ-3 | R5 |
| 5.5 | Event emitter | Emit every decision as `agentwatch.security_event.v1` (`policy.decision`) with a join key | emitter | decision and record join on a common id | #69 | CUJ-3 | R6 |
| 5.T | Tests | Explain completeness, actionability test, reason codes, event schema conformance | tests | coverage ≥ 95% | #70 | CUJ-3 | R5, R6 |
| 5.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #71 | — | — |
| 5.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #72 | — | — |
| 5.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #73 | — | — |
| 5.D | Docs | Explain design + reference (reason codes) + event-binding note | docs | updated + linked | #74 | — | — |
| 5.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 5.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] 100% of denies traceable to a clause + context; the actionability test passes (**CUJ-3**)
- [ ] Every decision emitted in the agentwatch schema and joins on a common id (R6)

---

Part 3 green ⇒ the packs that stop real incidents ship, and every decision explains itself; proceed to
[Part 4 (M6–M7)](wbs-v0.1.0-part4-audit-ask.md).
