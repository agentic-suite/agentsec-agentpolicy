# Step-up, AuthZEN Interop & Adversarial Suite — Design (M14, v0.1.0)

**BLUF:** M14 makes the PDP **interop-standard** and **bypass-resistant**. It exposes a conformant **AuthZEN
Authorization API 1.0** surface (`POST /access/v1/evaluation` + boxcarring + decision context), reacts to a
403/authorization challenge with a **least-privilege step-up** (narrower scope + AuthZEN `acr_values`), serves the
**human gate over MCP** (a non-Python host asks the same question and gets the same decision), and proves the
engine cannot be tricked — an **adversarial suite** where every attempted bypass blocks with a distinct reason.
This is the design of record (`14.D0`); it delivers **CUJ-11**, **CUJ-14**, **CUJ-19** (R11, R26, R27).

> Status: **Done** — branch `feat-0.1.0`. Modules: `authzen.py`, `stepup.py`, `server/mcp_tools.py`,
> `server/pdp_routes.py` (peer).

---

## 1. AuthZEN Authorization API 1.0 (`14.2`)

`agentpolicy/authzen.py` — `POST /access/v1/evaluation` (registered via
`register_authzen_routes`). An AuthZEN request `{subject, action, resource, context}` maps to the same
`ServerCore.evaluate` call as every other surface and returns an AuthZEN response:

```json
{ "decision": false,
  "context": { "schema": "authzen.evaluation.v1",
               "reason_code": "deny_critical_op",
               "reason_admin": { "reason_code": "deny_critical_op", "policy_version": "0.1.0" },
               "reason_user": "…" } }
```

* **Decision:** `true` for `allow`/`audit`/`redact`, `false` otherwise — the boolean AuthZEN contract.
* **Decision context:** the machine `reason_code` + `policy_version` (operator) and a `reason_user` sentence.
* **Boxcarring:** `{evaluations: [...], options: {evaluations_semantic}}` evaluates many requests in one call with
  the semantic `execute_all` / `deny_on_first_deny` / `permit_on_first_permit`; the batch also returns an overall
  `decision`.

The mapping (`_call_kwargs`) reads fields from the top level **or** the AuthZEN `properties` bag, so
`resource.id`/`resource.properties.tool`, `action.name`/`action.properties.verb`, and
`resource.properties.{environment,data_class}` all work.

## 2. Scope-escalation / step-up (`14.1`)

`agentpolicy/stepup.py` — `is_challenge(status_code)` (a 403 triggers step-up). `step_up(decision, call,
evaluator)` turns a denial into a **least-privilege** `StepUpRequest`: the narrowed scope is the M5
**actionability variant** (`explain.flip_variant`), so it is *verified* to change the outcome, and it carries the
AuthZEN `acr_values` marker `urn:agentpolicy:stepup:narrow-scope`. The loop is least-privilege **by
construction** — the narrowed request only *removes* scope (production→staging, destructive→read-only, lower data
class), never adds it.

## 3. MCP-server ask path (`14.3`)

`server/mcp_tools.py` registers four tools backed by the M12/M7 ask broker (`ServerCore.ask_broker`):
`agentpolicy.ask_create`, `agentpolicy.approve`, `agentpolicy.deny`, `agentpolicy.ask_resolve`. A non-Python MCP
host can create a pending ask, resolve it, and re-submit — and gets the **same resolution** as an in-process
`AskBroker.resolve` on the same store (parity test).

## 4. Adversarial resilience suite (`14.4`)

`tests/test_m14_m14.py` consolidates the attack classes and asserts each **blocks with a distinct reason**:

| Class | Attempt | Outcome |
|---|---|---|
| injection | hidden instructions in a tool description | flagged (`scan_tool_definition`) |
| obfuscation | case/whitespace-unfolded tool name | folded to the real (dangerous) tool → deny |
| dispatcher | `git push --force` smuggled via a coarse command | canonicalized to `force_push` → deny |
| replay | an approval reused for a different call | `deny_action_identity_mismatch` |
| tamper | an edited audit entry | chain verification fails |
| flood | a burst above the rate limit | `rate-limit` (`rate_limited`) |

The engine **never** silently allows: every failure path carries a distinct, non-empty reason code.

## 5. WBS M14 item mapping

| Item | Where |
|---|---|
| 14.D0 design docs first | this document |
| 14.1 scope-escalation/step-up | `agentpolicy/stepup.py` |
| 14.2 AuthZEN Authorization API 1.0 | `agentpolicy/authzen.py`, `server/cli.py` |
| 14.3 MCP-server ask path | `server/mcp_tools.py`, `ServerCore.ask_broker` |
| 14.4 adversarial resilience suite | `tests/test_m14_m14.py` |
| 14.T/14.C/14.L/14.CR/14.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [AuthZEN reference](../reference/authzen.md) |
