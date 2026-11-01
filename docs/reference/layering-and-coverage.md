# Narrow-only layering & action-space coverage — reference (v0.1.0)

WBS M21 · CUJ-30 / CUJ-31 · R44 / R45. Design:
[layering-and-coverage.md](../design/layering-and-coverage.md).

## Narrow-only layering (`21.1`, `21.2`)

```sh
agentpolicy check project.yaml --parent org.yaml   # fails (exit 2) if project widens org
```

```python
from agentpolicy.layering import Layer, compose, narrow_only_violations
from agentpolicy.policy.models import default_policy

org = default_policy("balanced")
effective = compose([Layer("org", org), Layer("project", project)])
narrow_only_violations(org, project)   # [] if the child only restricts; else one finding per widening allow
```

The effective policy is the **intersection**: rules are concatenated parent-first, so a **deny in any layer
wins**. A child `allow` that grants a scope the parent never allowed is a **widening** and fails `check` at PR
time, naming the rule. A child `deny` / `escalate` / narrowed `allow` is fine.

## Action-space coverage (`21.3`)

```sh
agentpolicy report coverage --inventory last-week.jsonl --out-of-scope rotate,index
```

```python
from agentpolicy.coverage import coverage_report, inventory_from_events
report = coverage_report(policy, inventory={"rotate": 3, "read": 5})
report.dangerous          # exercised but uncovered (the dangerous quadrant)
report.dead               # covered but never exercised
report.gap_unexplained     # |dangerous| minus the explicitly out-of-scope verbs
```

Four quadrants: covered+exercised (good), covered+never (**dead**), **uncovered+exercised (dangerous, named
loudly)**, uncovered+never. The honesty contract is **`gap_unexplained == 0`** — every dangerous verb is either
covered or declared out-of-scope. The `--inventory` file is a JSONL window of agentwatch events.
