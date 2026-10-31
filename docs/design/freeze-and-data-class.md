# Freeze Windows & Data-Class Derivation — Design (M15, v0.1.0)

**BLUF:** M15 expresses the exact Replit condition: a **declared, audited freeze** tightens the posture for its
window (a write in production becomes `ask`/`deny` while the freeze is active) and stamps a `freeze_id` on the
decision. It also **derives `data_class`** deterministically from globs / resource tags / schema hints so adopters
do not hand-tag everything — and a **conflict fails loudly**, never silently. This is the design of record
(`15.D0`); it delivers **CUJ-21** (R33, R34).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/freeze.py`, `agentpolicy/data_class.py`,
> `cli/freeze.py`, `packs/code-freeze/`.

---

## 1. Freeze windows (`15.1`)

`agentpolicy/freeze.py`:

* `FreezeWindow(freeze_id, environments, starts_at, ends_at, reason)` — a declared window over one or more
  environments; `is_active(at, environment)`.
* `FreezeLedger` — `declare(...)` (mints a `frz_` id and records a `declare` **audit event**), `expire(freeze_id,
  at)` (records an `expire` event), `active_freeze(environment, at)` (returns the governing window), and `events`
  (the audited on/off trail).
* **Overlap — strictest wins.** When two windows cover the same environment the **narrower** scope wins (fewest
  environments), and on a tie the earlier `starts_at`; the resolution is deterministic and documented.

The engine carries an optional ledger. On `evaluate`, if a window is active for the call's environment the
decision is **tightened**: an otherwise-allowed/audited **write** becomes `escalate` with reason code
`freeze_active` and an explanation naming the `freeze_id`; every decision in a frozen environment carries
`freeze_id` (provenance). The `freeze` CLI (`declare`/`expire`/`list`) manages the ledger, and on/off is audited.

The shipped **`packs/code-freeze`** pack carries the same rule class in Cedar
(`@id("code-freeze-block")`, keyed on `context.freeze_id`), proven by its `tests.yaml` replay (fixtures supply the
`freeze_id` context).

## 2. Data-class derivation (`15.3`)

`agentpolicy/data_class.py`:

* `DataClassRule(pattern, data_class)` — a glob (`fnmatch`) over the resource path/id.
* `derive_data_class(resource, rules, *, tags=None, schema_hint=None)` — resolves a class in a **fixed
  precedence**: an explicit **tag** wins, then the first matching **glob**, then a **schema hint**. It returns
  `None` when nothing matches (the caller falls back to its default).
* **Conflict fails loudly:** if two rules of the same precedence match with **different** classes,
  `DataClassConflictError` is raised — the derivation never silently picks one.

The engine accepts `data_class="auto"` and derives it from the policy's `data_class_rules` + the call's
`resource_tag`/arguments before normalization, so an untagged resource resolves deterministically.

## 3. WBS M15 item mapping

| Item | Where |
|---|---|
| 15.D0 design docs first | this document |
| 15.1 freeze windows | `agentpolicy/freeze.py`, `cli/freeze.py`, `engine/engine.py` |
| 15.2 freeze policy pack | `packs/code-freeze/` |
| 15.3 data-class derivation | `agentpolicy/data_class.py`, `policy/{models,schema,loader}.py`, `engine/engine.py` |
| 15.T/15.C/15.L/15.CR/15.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [freeze/data-class reference](../reference/freeze-and-data-class.md) |
