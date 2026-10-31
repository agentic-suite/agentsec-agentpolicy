# Postures, init, diff, lint & export — reference (v0.1.0)

WBS M9 · CUJ-8 / CUJ-16 / CUJ-17 · R12 / R16. Design: [postures-lint-export.md](../design/postures-lint-export.md).

## Posture presets

Three presets ship: `strict`, `balanced` (default), `permissive`. `init` writes a **commented** `agentpolicy.yaml`
that is an overlay on the preset — never a blank policy.

```sh
agentpolicy init --posture strict -o agentpolicy.yaml
agentpolicy init --posture balanced -o agentpolicy.yaml --scaffold-dir ./scaffold --adapter raw
```

`--scaffold-dir` also writes `adapter.py` (a ready guard using the chosen adapter) and `QUICKSTART.md`.

## `agentpolicy diff` — kept / overridden / gaps

```sh
agentpolicy diff agentpolicy.yaml
agentpolicy diff agentpolicy.yaml --json
```

Classifies every environment / data class / risk weight / rule as **kept**, **overridden**, or a **gap** (present
in the default, absent from the overlay). Exit 0 when the policy matches the default, 1 otherwise.

## `agentpolicy lint` — CI-failable

```sh
agentpolicy lint agentpolicy.yaml          # exit 1 when any finding
agentpolicy lint agentpolicy.yaml --json
```

| Code | Severity | Meaning |
|---|---|---|
| `unreachable_rule` | warning | a rule shadowed by an earlier, broader rule of the same decision |
| `over_permissive_allow` | error | an `allow` rule with no constraints |
| `unknown_tool_rule` | warning | a rule naming a tool not in the taxonomy |
| `outcome_conflict` | error | two rules with identical constraints, conflicting decisions |
| `literal_secret` | error | a secret/PII literal in the policy text |

## `agentpolicy export` — policyweave handoff

```sh
agentpolicy export --format cedar                       # Cedar source
agentpolicy export --format policyweave -o policy.json  # compiled artifact
```

* `cedar_source(policy)` → one `permit`/`forbid` per rule, each with a comment carrying the rule's reason.
* `export_policy(policy, target="policyweave")` → `{target, schema, version, posture, policy_hash, cedar, rules[],
  environments, data_classes}` — the compiled artifact a harness/policyweave consumes.

```python
from agentpolicy.export import cedar_source, export_policy
from agentpolicy.policy.models import default_policy

cedar = cedar_source(default_policy("balanced"))
artifact = export_policy(default_policy("balanced"))     # policyweave.policy.v1
```
