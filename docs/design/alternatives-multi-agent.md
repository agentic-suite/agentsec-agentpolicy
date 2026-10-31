# Nearest-Permissible-Action & Multi-Agent Governance — Design (M17, v0.1.0)

**BLUF:** M17 makes denials **replan-able** and multi-agent systems **provable**. Every deny/ask carries
**verified-permissible alternatives** (`permitted_alternatives[]`) the agent can retry immediately — evaluated-true
against the policy and **agent-facing** (no policy internals). Delegation chains are **scope-subset-proven**
(`delegation_chain` in the principal; an out-of-scope child is denied naming the link), and an **agent→agent
request** is decided through the same engine. This is the design of record (`17.D0`); it delivers **CUJ-24**,
**CUJ-28** (R37, R39, R25).

> Status: **Done** — branch `feat/0.1.0`. Modules: `agentpolicy/explain.py`,
> `engine/delegation.py`, `engine/engine.py`, `packs/multi-agent-delegation/`.

---

## 1. `permitted_alternatives[]` (`17.1`)

`explain.permitted_alternatives(decision, call, evaluator)` returns the variants the agent can replan to
**immediately**. Each is:

* **verified-permissible** — re-evaluated against the policy; only `allow`/`redact`/`ask` variants are returned
  (the PDP never suggests something it would itself deny);
* **agent-facing** — `{action, environment, data_class, outcome, description}`, the action's own fields plus a
  curated sentence, and **no policy internals** (no matched rule, condition, or clause).

The alternatives are attached to the `ExplainArtifact` (`to_dict()["permitted_alternatives"]`) and skip duplicates;
an `allow` has none. This is the operator/agent split: the operator sees the clause and factors, the agent sees
the curated, replan-able set.

## 2. Delegation-chain + scope-subset (`17.2`)

`DelegationManager.effective_environments(child_id, policy)` intersects the requested scope of **every link** in
the child's chain with each ancestor's profile scope; it returns `None` when the identity is not a delegated
child (no constraint) and `()` when the chain imposes none. The engine adds a delegation-scope stage: an action
outside the child's effective environments is **denied** naming the chain link
(`agent 'child' (chain root > child) is not scoped to environment 'production' (allowed: ['staging'])`). The
`delegation_chain` travels on the principal context.

## 3. Inter-agent decisions (`17.3`)

`Engine.inter_agent(source_id, target_id, environments=…)` treats an agent invoking/creating another agent as
**any other action**: it runs the delegation scope-subset proof and returns a `Decision` (`allow` with
`allow_delegation`, or `deny` with `deny_delegation_exceeds_scope`).

## 4. `multi-agent-delegation` pack (`17.4`)

`packs/multi-agent-delegation` ships the scope rule as Cedar (`@id("multi-agent-delegation-gate")`, keyed on
`context.delegation_chain`), proven by its `tests.yaml` replay (a delegated child's production write denied; a
non-delegated write gated; a non-delegated staging read allowed).

## 5. WBS M17 item mapping

| Item | Where |
|---|---|
| 17.D0 design docs first | this document |
| 17.1 `permitted_alternatives[]` | `agentpolicy/explain.py` |
| 17.2 delegation-chain + scope-subset | `engine/delegation.py`, `engine/engine.py` |
| 17.3 inter-agent decisions | `engine/engine.py` (`inter_agent`) |
| 17.4 `multi-agent-delegation` pack | `packs/multi-agent-delegation/` |
| 17.T/17.C/17.L/17.CR/17.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [alternatives/multi-agent reference](../reference/alternatives-and-multi-agent.md) |
