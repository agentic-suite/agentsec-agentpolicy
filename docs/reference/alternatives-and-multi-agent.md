# Nearest-permissible-action & multi-agent governance — reference (v0.1.0)

WBS M17 · CUJ-24 / CUJ-28 · R37 / R39 / R25. Design:
[alternatives-multi-agent.md](../design/alternatives-multi-agent.md).

## Permitted alternatives (`17.1`)

```python
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.explain import build_artifact

evaluator = CedarEvaluator()
call = canonicalize(tool="drop_database", action="delete", environment="production",
                    data_class="customer_pii", agent_id="release-bot")
artifact = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator)
artifact.to_dict()["permitted_alternatives"]
# [{"action": "read", "environment": "production", "data_class": "customer_pii",
#   "outcome": "redact", "description": "Retry as a read action in production (would be redact)."}]
```

Each alternative is **evaluated-true** and **agent-facing** (no rule/condition/clause) — the model can retry
immediately. An `allow` returns none.

## Delegation scope (`17.2`)

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import AgentProfile, default_policy
from dataclasses import replace

base = default_policy("balanced")
policy = replace(base, agents={**base.agents,
                               "parent": AgentProfile("ci-bot", 0.1, environments=("staging",))})
engine = Engine(policy)
engine.delegate("child", "parent", environments=("staging",))     # allowed

engine.evaluate(tool_name="query_logs", action="read", environment="production",
                data_class="internal", agent_id="child").reason_code
# "deny_delegation_exceeds_scope" — names the chain (root > child)
```

`DelegationManager.effective_environments(child_id, policy)` → the intersection of the chain's scopes (`None` when
not a delegated child, `()` when unrestricted).

## Inter-agent decisions (`17.3`)

```python
engine.inter_agent("parent", "target", environments=("staging",)).reason_code   # "allow_delegation"
engine.inter_agent("parent", "target", environments=("production",)).decision   # "deny"
```

An agent→agent request is decided like any action (the delegation scope-subset proof).

## Pack (`17.4`)

`packs/multi-agent-delegation` carries `@id("multi-agent-delegation-gate")` — a delegated child (`delegation_chain`
non-empty) may not act in production.
