# AuthZEN, step-up & adversarial resilience — reference (v0.1.0)

WBS M14 · CUJ-11 / CUJ-14 / CUJ-19 · R11 / R26 / R27. Design:
[stepup-authzen-adversarial.md](../design/stepup-authzen-adversarial.md).

## AuthZEN Authorization API 1.0 (`14.2`)

```sh
agentpolicy serve          # exposes POST /access/v1/evaluation (+ /authorize)
```

```json
POST /access/v1/evaluation
{ "subject":  { "type": "agent", "id": "release-bot" },
  "action":   { "name": "delete" },
  "resource": { "type": "tool", "id": "drop_database",
                "properties": { "environment": "production", "data_class": "customer_pii" } } }
```

Response:

```json
{ "decision": false,
  "context": { "schema": "authzen.evaluation.v1", "reason_code": "deny_critical_op",
               "reason_admin": { "reason_code": "deny_critical_op", "policy_version": "0.1.0" },
               "reason_user": "…" } }
```

**Boxcarring:**

```json
{ "evaluations": [ {…}, {…} ],
  "options": { "evaluations_semantic": "deny_on_first_deny" } }
```

→ `{ "evaluations": [ … ], "decision": false }`. Semantics: `execute_all` (all must permit),
`deny_on_first_deny`, `permit_on_first_permit`.

The decision is the **same** as every other surface (library/CLI/MCP) — the route delegates to `ServerCore`.

## Step-up (`14.1`)

On a `403` authorization challenge, narrow the scope and re-issue with a step-up context:

```python
from agentpolicy.stepup import is_challenge, step_up

if is_challenge(403):
    request = step_up(decision, call, evaluator)     # least-privilege, verified
    request.acr_values   # ("urn:agentpolicy:stepup:narrow-scope",)
    request.narrowed     # the narrowed canonical action (e.g. delete->read, production->staging)
```

The narrowed scope is derived from the M5 actionability search, so it is **verified** to change the outcome; it
only ever *removes* scope.

## MCP ask path (`14.3`)

MCP tools (backed by the ask broker): `agentpolicy.ask_create`, `agentpolicy.approve`, `agentpolicy.deny`,
`agentpolicy.ask_resolve`. A non-Python host gets the same resolution as in-process.

## Adversarial resilience (`14.4`)

| Class | Blocked with |
|---|---|
| injection | scanner finding |
| obfuscation | folded to the real tool → policy deny |
| dispatcher smuggling | canonicalized → deny |
| replay | `deny_action_identity_mismatch` |
| tamper | audit chain verification fails |
| flood | `rate-limit` (`rate_limited`) |

Every failure path carries a **distinct, non-empty** reason code — no silent allows.
