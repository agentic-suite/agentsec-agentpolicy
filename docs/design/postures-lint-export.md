# Posture Presets, init, diff & lint — Design (M9, v0.1.0)

**BLUF:** M9 makes policy authoring **never a blank slate**. Three **posture presets** (`strict` / `balanced` /
`permissive`) ship as commented, pre-populated policies; `init` scaffolds a policy **and** an adapter hint **and**
a quickstart; `diff` classifies kept / overridden / **gaps**; **lint** reports unused / shadowed / over-permissive
/ cross-pack-conflict / literal-secret findings with locations (CI-failable); and `export` emits the Cedar source
+ compiled artifacts for a **policyweave** handoff. This is the design of record (`9.D0`); it delivers
**CUJ-8**, **CUJ-16**, **CUJ-17** (R12, R16).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/lint.py`, `agentpolicy/export.py`,
> `policy/postures.py` (commented presets), `cli/{init,diff,lint,export}.py`.

---

## 1. Posture presets (`9.1`)

`strict` / `balanced` / `permissive` remain the single source of truth (`default_policy(posture)`); the shipped
YAML presets and `init` output are **commented** (a header explains the posture and that the file is an overlay on
the preset), so an operator edits a populated, documented policy — never a blank one. `render_preset(name)` emits
the commented document; `load_policy_text(render_preset(name)) == default_policy(name)` still holds (comments are
ignored by the loader), so there is no drift.

## 2. `init` scaffold (`9.2`)

`agentpolicy init --posture <name> [-o PATH] [--adapter NAME] [--scaffold-dir DIR]`:

* writes the commented `agentpolicy.yaml` (as today), and
* when `--adapter` / `--scaffold-dir` is given, also writes an **adapter stub** and a **QUICKSTART.md** so the
  operator has a runnable first step (the "policy + adapter + quickstart" deliverable). The default
  (no flags) behaviour is unchanged, so existing callers keep working.

## 3. `agentpolicy diff` (`9.3`)

`diff` compares the loaded policy against its posture default and classifies every entry as **kept**
(equal to the default), **overridden** (changed), or a **gap** (present in the default, absent from the overlay).
Top-level sections, environments, data classes, risk weights, and **per-rule** differences are reported.
`--json` emits the structured diff for CI. Exit code: 0 when no overrides/gaps, 1 otherwise (unchanged).

## 4. Rule/policy lint (`9.4`)

`agentpolicy/lint.py` — deterministic, no ML. `lint_policy(policy) -> list[Finding]`:

| Finding code | Meaning |
|---|---|
| `unreachable_rule` | a rule that can never fire (shadowed by an earlier, broader rule) |
| `over_permissive_allow` | an `allow` rule with no constraints (`tool`/`action`/`environment`/`data_class` all `*`) |
| `unknown_tool_rule` | a rule naming a tool not in the taxonomy |
| `outcome_conflict` | two rules with the same constraints but conflicting decisions (cross-pack conflict) |
| `literal_secret` | a secret/PII literal found in the policy text |

`Finding(code, severity, message, location)` with a human `location` (e.g. `rules[2]`, `reason`). `severity` is
`error` (must fix) or `warning`. `lint_text(text)` scans raw policy text for literal secrets. `agentpolicy lint
[PATH] [--json]` prints findings with locations and **exits 1 when any finding exists** (CI-failable).

## 5. Policy export (policyweave) (`9.5`)

`agentpolicy/export.py`:

* `cedar_source(policy) -> str` — render a loaded `Policy` to Cedar text (one `permit`/`forbid` per rule, with a
  comment carrying the rule's human reason).
* `export_policy(policy, target="policyweave") -> dict` — `{target, schema, version, posture, policy_hash,
  cedar, rules[], environments, data_classes}`; the "compiled artifact" a harness/policyweave consumes.
* `agentpolicy export [--policy PATH] [--format cedar|policyweave] [-o OUT]` — one policy → harness formats.

## 6. WBS M9 item mapping

| Item | Where |
|---|---|
| 9.D0 design docs first | this document |
| 9.1 posture presets | `policy/postures.py` (commented presets) |
| 9.2 `init` scaffold | `cli/init.py` |
| 9.3 `agentpolicy diff` | `cli/diff.py` |
| 9.4 rule-pack lint | `agentpolicy/lint.py`, `cli/lint.py` |
| 9.5 policy export (policyweave) | `agentpolicy/export.py`, `cli/export.py` |
| 9.T/9.C/9.L/9.CR/9.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [postures/lint reference](../reference/postures-and-lint.md) |
