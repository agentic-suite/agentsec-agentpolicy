# Shadow mode, calibration & canary — reference (v0.1.0)

WBS M10 · CUJ-4 · R30. Design: [shadow-calibration-canary.md](../design/shadow-calibration-canary.md).

## Shadow mode (`10.1`)

`Engine(dry_run=True)` logs the **real** decision but returns `allow` to the caller — the agent never sees the
shadow verdict, and operators see what *would have happened*.

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

engine = Engine(default_policy("balanced"), dry_run=True)
decision = engine.evaluate(tool_name="drop_database", action="delete",
                           environment="production", data_class="customer_pii",
                           agent_id="release-bot")
decision.decision   # "allow"
decision.dry_run    # True
# the audit trail records the real "deny"
```

## Inspect what would have been blocked (`10.2`)

```sh
agentpolicy audit query --dry-run
agentpolicy audit query --dry-run --decision deny --format csv
```

Filters the audit trail to shadow (`dry_run`) decisions — the would-have-blocked / would-have-escalated set.

## Calibration report (`10.3`)

```sh
agentpolicy calibrate report          # buckets + shadow rates
agentpolicy calibrate report --json
```

`calibration.calibrate(entries)` computes, over the **shadow** decisions:

| Field | Meaning |
|---|---|
| `shadow` | decisions recorded in shadow mode |
| `would_block` / `false_block` / `false_block_rate` | blocked decisions near the allow boundary (counterfactual ≤ 0.5) |
| `allowed` / `false_miss` / `false_miss_rate` | allows near the block boundary (counterfactual ≥ 0.75) |
| `threshold_table` | the counterfactual-threshold distribution |

With no ground truth, the rates are an explicit, deterministic **counterfactual heuristic** (documented in
`calibration.py`): a block whose governing boundary is low is a false-block candidate; an allow near the critical
boundary is a false-miss candidate.

## Canary rollout (`10.4`)

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.canary import CanaryConfig, canary_selected, STAGES   # (5, 50, 100)

Engine(policy, canary_percent=5)     # enforce for 5% of sessions; shadow the rest
canary_selected("sess_abc", 50)      # deterministic — same answer every run/machine
```

Selection is a **stable hash of the session id** (`sha256` → `[0, 100)`), so a session never flickers between
enforced and shadowed, and a rollout is reproducible. `canary_percent=0` disables the canary (full enforce — the
historical behaviour); `100` enforces for everyone; a missing session id is treated as not selected until `100`.
