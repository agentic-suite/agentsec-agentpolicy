# Freeze windows & data-class derivation — reference (v0.1.0)

WBS M15 · CUJ-21 · R33 / R34. Design: [freeze-and-data-class.md](../design/freeze-and-data-class.md).

## Freeze windows (`15.1`)

```sh
agentpolicy freeze declare --env production --until 2026-11-01T00:00:00+00:00 --reason "release"
agentpolicy freeze list --json
agentpolicy freeze expire frz_ab12…
```

While a window is active for an environment, the engine **tightens** the posture — a write becomes `escalate` with
`reason_code="freeze_active"` — and every decision in that environment carries `freeze_id`. Declare/expire are
audited events (`FreezeLedger.events`). Overlap: the **narrowest** scope wins (deterministic).

```python
from agentpolicy.freeze import FreezeLedger
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

ledger = FreezeLedger()
ledger.declare(environments=["production"], ends_at="2026-11-01T00:00:00+00:00", reason="release")
engine = Engine(default_policy("balanced"), freeze_ledger=ledger)
engine.evaluate(tool_name="deploy_service", action="write", environment="production",
                data_class="internal", agent_id="release-bot").reason_code  # "freeze_active"
```

The shipped `packs/code-freeze` pack carries the same rule class in Cedar (`@id("code-freeze-block")`, keyed on
`context.freeze_id`).

## Data-class derivation (`15.3`)

```yaml
data_class_rules:
  - { pattern: "*/secrets/*",  data_class: customer_pii }
  - { pattern: "srv/*.sql",    data_class: restricted }
```

```python
from agentpolicy.data_class import DataClassRule, derive_data_class

derive_data_class("srv/secrets/db", [DataClassRule("*/secrets/*", "customer_pii")])
# "customer_pii"
```

Precedence: explicit **tag** → **glob** → **schema hint** → `None`. Pass `data_class="auto"` to `evaluate` and the
engine derives it from the policy rules + `resource_tag`. A **conflict** (two tags, or two globs, with different
classes) raises `DataClassConflictError` → the engine fails closed with `deny_data_class_conflict`.
