# Break-glass & dual-control — reference (v0.1.0)

WBS M18 · CUJ-25 / CUJ-26 · R40 / R41. Design:
[breakglass-and-dual-control.md](../design/breakglass-and-dual-control.md).

## Break-glass elevation (`18.1`, `18.2`)

```sh
agentpolicy breakglass elevate --agent incident-bot --env production --until 2026-11-01T00:00:00+00:00 \
    --reason "SEV-1 mitigation"
agentpolicy breakglass list --json
agentpolicy breakglass revert bg_ab12…
```

An elevation is **time-boxed**, **requires a logged reason** (never silent), and **reverts automatically at
expiry**. Every decision made while a window elevates the agent carries `break_glass_id`.

```python
from agentpolicy.breakglass import BreakGlassLedger
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

ledger = BreakGlassLedger()
ledger.elevate(agent_id="incident-bot", environments=["production"],
               ends_at="2026-11-01T00:00:00+00:00", reason="SEV-1 mitigation")
engine = Engine(default_policy("balanced"), break_glass_ledger=ledger)
decision = engine.evaluate(tool_name="query_logs", action="read", environment="production",
                           data_class="internal", agent_id="incident-bot")
decision.break_glass_id      # "bg_…"
```

**Widens scope ceilings only.** A window waives the identity-environment scope and the delegation-scope proof;
it **never** bypasses the mandatory human gate. `BreakGlassLedger.sweep()` (called on read) auto-reverts every
expired window and appends a `revert` audit event without any manual action.

## Dual-control approvals (`18.3`, `18.4`)

The irreversible / mandatory human-gate class needs a **quorum (default 2) of distinct approvers**. A record is
bound to the call's `action_identity` and a TTL still applies.

```python
from agentpolicy.dualcontrol import DualControlGate

gate = DualControlGate(quorum=2)
rec = gate.request(call)                     # e.g. escalation → decision.dual_control_id
gate.approve(rec.dual_control_id, approver="alice")
gate.released(rec.dual_control_id)           # False — one approval is not a release
gate.approve(rec.dual_control_id, approver="bob")
gate.released(rec.dual_control_id)           # True
gate.resolve(rec.dual_control_id, call=call) # {"status": "allow", …}
```

A repeat approval by the **same** principal is rejected (`ValueError`) — one human cannot make quorum. The
engine opens a quorum record for a human-gate-class escalation and stamps `dual_control_id` on the decision.

**Composition guard.** Break-glass and dual-control compose: a window does **not** waive an escalation, so an
irreversible action still needs its quorum *inside* a break-glass window. Reason codes:
`dual_control_required`, `deny_dual_control_pending`, `deny_dual_control_unknown`, `allow_dual_control_approved`.
