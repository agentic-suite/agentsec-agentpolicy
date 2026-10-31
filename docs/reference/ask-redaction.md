# Ask round-trip, redaction & secrets-in-args — reference (v0.1.0)

WBS M7 · CUJ-10 / CUJ-15 · R18 / R20 / R38. Design: [ask-redaction.md](../design/ask-redaction.md).

## The ask round-trip

A Cedar `ask` decision is a pending human gate. The engine creates an `Ask` bound to the exact
`(tool, action, arguments)` identity; a human resolves it with the CLI; the agent resumes by re-submitting the
call with the `ask_id`.

```sh
agentpolicy ask list
agentpolicy ask list --json
agentpolicy approve ask_ab12… --approver alice
agentpolicy deny    ask_ab12… --approver alice --reason "not this quarter"
```

Store: `~/.agentpolicy/asks.json` (override with `--store` or `AGENTPOLICY_ASKS_FILE`).

### Resolution outcomes

| Situation | Result | `reason_code` |
|---|---|---|
| approved, matching action identity | allow | `allow_ask_approved` |
| denied by a human | deny | `deny_ask_denied` |
| TTL elapsed (**timeout = deny**) | deny | `human_gate_timeout` |
| still pending (no approval) | deny | `deny_ask_pending` |
| unknown `ask_id` | deny | `deny_ask_unknown` |
| approval reused for a different call | deny | `deny_action_identity_mismatch` |

An approval is bound to the exact `(tool, action, arguments)` identity — an approval for X cannot release Y.

## Python

```python
from agentpolicy.ask import AskBroker, gate
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator

broker = AskBroker(ttl_seconds=300)
call = canonicalize(tool="deploy_service", action="write", environment="production",
                    data_class="restricted", agent_id="release-bot")
decision, ask = gate(CedarEvaluator().evaluate(call), call, broker)   # decision.ask_id set
broker.approve(ask.ask_id, approver="alice")
result = broker.resolve(ask.ask_id, call=call)                        # {"status": "allow", …}
```

## Redact-and-allow (`7.3`)

Scrub secrets/PII from a tool result before it reaches the model. The raw value is never returned; each class
matched yields a **receipt** (`class` / `count` / `locations`).

```python
from agentpolicy.redaction import redact_output

scrubbed, receipts = redact_output("token=sk-proj-…")
# scrubbed has [REDACTED-SECRET]; receipts == [{"class": "secret", "count": 1, "locations": ["output"]}]
```

## Secrets-in-arguments (`7.4`)

Scrub secrets/PII pasted into argument **values** (not just sensitive key names) before the call leaves. Composes
with the key-based audit redactor.

```python
from agentpolicy.redaction import redact_argument_values

scrubbed, receipts = redact_argument_values({"command": "curl -H 'Authorization: Bearer sk-…'"})
# scrubbed["command"] has [REDACTED-SECRET]; receipts carry class/count/location
```

| Class | Examples the scanner catches |
|---|---|
| `secret` | `sk-…`, `AKIA…`, `ghp_…`/`github_pat_…`, Slack `xox…`, JWT, private key, Google API key |
| `pii` | SSN, credit card number |

The pattern set is the single source shipped by `engine/output_inspector.py`.
