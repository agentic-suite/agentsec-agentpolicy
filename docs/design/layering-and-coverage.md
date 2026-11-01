# Narrow-Only Layering & Action-Space Coverage — Design (M21, v0.1.0)

**BLUF:** M21 lets a central team own an **org baseline** while project and session layers can only **restrict**
— a widening overlay **fails `agentpolicy check` at PR time**, naming the rule (the AWS SCP pattern, enforced at
load, never a runtime surprise). It also ships the **action-space coverage report** — the canonical taxonomy
crossed with the rules and the fleet inventory — which names the **exercised-but-uncovered** quadrant loudly.
This is the design of record (`21.D0`); it delivers **CUJ-30** and **CUJ-31** (R44, R45).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/layering.py`, `agentpolicy/coverage.py`,
> `cli/check.py` (`--parent`), `cli/report.py` (`report coverage`).

---

## 1. Layered composition (`21.1`)

`agentpolicy/layering.py`:

* `Layer(name, policy)` — one layer, named `org` / `project` / `session` in order.
* `compose(layers) -> Policy` — the **effective policy** is the *intersection*: rules are concatenated
  **parent-first**, so the decision cascade (deny > allow > escalate) makes a **deny in any layer win** — the
  union of restrictions, the intersection of permits. Non-rule fields (environments / data classes / agents)
  come from the **org** layer, so a child cannot re-weight the floor's risk model either. Composition is
  deterministic (layer order is fixed).

## 2. The narrow-only invariant (`21.2`)

The invariant is **enforced at load**, not at decide: `narrow_only_violations(parent, child)` returns one
human-readable finding per child `allow` rule that is **not** covered by some parent `allow` rule — i.e. a child
`allow` that grants a scope the parent never allowed. The coverage test reuses `lint._broadens` (the rule-scope
containment already used by the lint `unreachable_rule` check — one definition, no drift).

A child `deny` / `escalate` / narrowed `allow` is **not** a violation: restricting is the whole point. The
`agentpolicy check POLICY --parent PARENT` surface runs the invariant and **fails (exit 2) naming the widening
rule**, so a widening overlay is a **PR-time failure**, never a runtime surprise.

## 3. Action-space coverage report (`21.3`)

`agentpolicy/coverage.py` crosses the canonical **taxonomy verbs** with (a) the policy **rules** and (b) the
**fleet inventory** (the verbs agentwatch actually recorded). Four quadrants:

| | exercised | never exercised |
|---|---|---|
| **covered** | covered + exercised (good) | covered + never (**dead** rule — lint's cousin) |
| **uncovered** | **uncovered + exercised — the dangerous quadrant, named loudly** | uncovered + never (declare out-of-scope or accept) |

A verb is **covered** when a rule references it (or a wildcard `action: "*"` rule does). A verb is
**exercised** when the inventory contains it. `CoverageReport.gap_unexplained = |dangerous|` — where
`dangerous` is uncovered+exercised **minus** the verbs explicitly declared `out_of_scope`. The honesty contract
is `gap_unexplained == 0`: every dangerous verb is either covered or declared out-of-scope.

`agentpolicy report coverage [--inventory FILE] [--out-of-scope v1,v2] [--json]` renders it; the inventory file
is a JSONL window of agentwatch events (same shape the backtest reads).

## 4. WBS M21 item mapping

| Item | Where |
|---|---|
| 21.D0 design docs first | this document |
| 21.1 layered composition | `agentpolicy/layering.py` (`compose`) |
| 21.2 narrow-only invariant | `narrow_only_violations`, `cli/check.py --parent` |
| 21.3 coverage report | `agentpolicy/coverage.py`, `cli/report.py coverage` |
| 21.T/21.C/21.L/21.CR/21.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [layering/coverage reference](../reference/layering-and-coverage.md) |
