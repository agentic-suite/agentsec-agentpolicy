# CLI Reference

`agentpolicy` — the pre-execution policy decision point CLI. Run `agentpolicy --help` for the live surface,
`agentpolicy <command> --help` for one command.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | general failure (decision deny is **not** a failure — it is a successful evaluation) |
| `2` | **invalid configuration/policy** (fail-closed) or a usage error |

## Global

```sh
agentpolicy --version          # agentpolicy 0.1.0
agentpolicy --help
```

## Commands

### evaluate — one call → one decision

```sh
agentpolicy evaluate --tool drop_database --action delete \
  --env production --data customer_pii --agent release-bot
```

Required: `--tool --action --env --data --agent`. Options: `--session`, `--dry-run` (shadow mode), `--format {table,json}`,
`--policy PATH`. Prints the decision, criticality, reason code, explanation, and factors.

### explain — factor breakdown + explanation (offline, Cedar)

```sh
agentpolicy explain --tool query_logs --action read --env staging --data internal --agent debug-bot
agentpolicy explain --tool drop_database --action delete --env production --data customer_pii --agent release-bot --json
```

Evaluates the call offline through the canonicalizer + Cedar decision core (no server, no network) and prints the
outcome, the machine `reason_code`, the matched rule/`clause`, the factor breakdown, and the one change that would
flip the outcome. `--json` prints the full explain artifact (the [reason-codes reference](reason-codes.md)).

### check — validate a policy file (fail-closed)

```sh
agentpolicy check ./agentpolicy.yaml          # exit 0 if clean, 2 if invalid
agentpolicy check ./agentpolicy.yaml --migrate # also report breaking changes vs the posture default
```

### init — write a posture preset

```sh
agentpolicy init --posture balanced           # balanced | strict | permissive  -> ./agentpolicy.yaml
agentpolicy init --posture strict -o policy.yaml
```

### doctor — environment checks + verdict

```sh
agentpolicy doctor [--policy PATH] [--json]   # exit 0 healthy / 1 unhealthy
```

### audit — query / show / replay / verify / evidence the trail

```sh
agentpolicy audit query [--decision deny] [--agent release-bot] [--format json|csv]
agentpolicy audit show --session <id>
agentpolicy audit session --replay <id>
agentpolicy audit verify [--sign]
agentpolicy audit evidence --tool drop_database --action delete --env production --data customer_pii --agent release-bot
```

`audit evidence` emits the offline-verifiable `EvidenceArtifact` (action + matched_rule + policy_version +
policy_hash + event_ref + hash). Entries carry their provenance (`policy_version`, `policy_hash`, `matched_rule`,
`seq`); `audit session --replay` verifies the whole hash chain before replaying. See [audit.md](audit.md).

### pack — validate + test rule packs

```sh
agentpolicy pack validate <dir>
agentpolicy pack test <dir>
agentpolicy pack list
```

### report — governance / compliance report

```sh
agentpolicy report [--type compliance|summary] [--period 2026-Q3|all] [--format html|csv]
```

### Others

`diff`, `policy` (rollback/inspect), `scan` (tool-definition scan), `analytics sessions`,
`calibrate report`, `baseline check`, `escalation` (review/approve), `swebench`, `test` (golden fixtures),
`serve` (MCP server), `field-test` (release-gate harness).

## In-process

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

engine = Engine(default_policy("balanced"))
decision = engine.evaluate(
    tool_name="query_logs", action="read",
    environment="staging", data_class="internal", agent_id="debug-bot",
)
print(decision.decision, decision.reason_code)
```
