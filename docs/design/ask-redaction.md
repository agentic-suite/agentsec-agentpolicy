# Ask round-trip, Redaction & Secrets-in-Args — Design (M7, v0.1.0)

**BLUF:** M7 makes the `ask` outcome **round-trip to a human** — action-identity-bound, expiring, and
**timeout = deny** — and makes redaction real: **redact-and-allow** scrubs secrets/PII from tool output with a
structured **receipt** (class/count/location), and **secrets pasted into arguments** are detected/scrubbed
*before* the call leaves the agent. Every scrub records a receipt; the raw secret is never persisted. This is the
design of record (`7.D0`); it delivers **CUJ-10**, **CUJ-15** (R18, R20, R38).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/ask.py`, `agentpolicy/redaction.py`,
> `cli/ask.py`; the ask record binds the Cedar `ask` outcome; the engine/user-facing steps are `approve`/`deny`.

---

## 1. The ask-gate broker (`7.1`)

The legacy `EscalationManager` (M3) tracks the ported `escalate` outcome. M7 adds the **ask broker** for the
Cedar `ask` outcome (`agentpolicy/ask.py`). It is the same proven round-trip, keyed on `ask_id`:

* `Ask` — `ask_id`, `status` (`pending`/`approved`/`denied`/`expired`), `action_identity`
  (`SHA-256(tool, action, canonical-args)` — the **same** function as escalation, one source of truth),
  `tool/action/environment/data_class/agent_id`, `reason`, `created_at`, `expires_at`, `approver`,
  `denied_reason`.
* `AskBroker.create(call, reason)` → a pending `Ask` with a `ask_`-prefixed unguessable id and a TTL
  (default 300 s).
* `approve(ask_id, approver)` / `deny(ask_id, approver, reason)` — reject unknown/already-resolved/expired ids
  and blank approvers.
* `resolve(ask_id, call)` → `{status, reason_code, explanation}`:
  * unknown → `human_gate_timeout`? no — unknown → deny `deny_ask_unknown`; expired → **`human_gate_timeout`**
    (timeout = deny); identity mismatch → `deny_action_identity_mismatch` (an approval for X cannot release Y);
    approved → allow; denied → `deny_ask_denied`; still pending → `deny_ask_pending` (replay).
* Persistence: `save`/`load` JSON (a human can approve an ask created by an earlier process).

**Wiring.** `ask.gate(decision, call, broker)` is the engine-facing hook: when the Cedar decision is `ask`, it
creates a pending record and stamps `decision.ask_id`; the caller returns the decision unchanged otherwise. The
`Decision` model gains an optional `ask_id`.

> **Timeout = deny.** `AskBroker.resolve` treats an expired ask as a deny with reason code
> `human_gate_timeout` (registered in the M5 registry) — an unanswered gate never silently allows.

## 2. `agentpolicy approve` / `agentpolicy deny` (`7.2`)

`cli/ask.py` registers two top-level commands (and `agentpolicy ask list` to see pending asks):

```sh
agentpolicy ask list
agentpolicy approve <ask_id> --approver alice
agentpolicy deny    <ask_id> --approver alice --reason "not this quarter"
```

The agent **resumes** by re-submitting the call with the `ask_id`; `AskBroker.resolve` returns the
approve/deny/timeout reason, and a denial carries the human's reason back to the agent.

## 3. Redact-and-allow (`7.3`)

`agentpolicy/redaction.py`:

* `RedactionReceipt` — `{class, count, locations[]}` where `class` is `secret` / `pii` / `credential`, and
  `locations` are field paths (`args.command`, `output`) or match spans. `to_dict()` is the durable receipt.
* `redact_text(text, *, classes=…, location="output") -> (scrubbed, receipts)` — scans the value for the known
  secret/PII patterns (`sk-…`, `AKIA…`, `ghp_…`, JWT, private key, SSN, credit card, email) and replaces each
  match with `[REDACTED-<CLASS>]`, emitting one receipt per class with the count.
* **The raw value is never returned or persisted** — only the scrubbed text and the receipts travel.

The Cedar `redact` outcome means "allow, scrub the output". `redaction.redact_output(decision, text)` applies
the scrub to a tool result and returns `(scrubbed, receipts)`; the receipts are attached to the audit entry.

## 4. Secrets-in-arguments (`7.4`)

`redaction.redact_argument_values(arguments, *, extra_keys=None) -> (scrubbed_args, receipts)` scans **argument
values** (free text), not just sensitive **key names** (the M5 audit redactor's job), so a secret pasted into
`args["command"]` or `args["body"]` is caught before the call leaves. It recurses into dicts/lists and composes
with the key-based redactor: the key-based redactor protects named fields; the value scanner protects pasted
content. Both emit receipts; neither persists the raw value.

## 5. Failure modes (loud, fail-closed)

* An unknown/expired/already-resolved ask is a **deny**, never an allow (timeout = deny).
* A blank approver is rejected (`ValueError`).
* A blank/absent `ask_id` on resolve is a deny (`deny_ask_unknown`).
* Argument scrubbing is best-effort but never *drops* a receipt: a class that matched is recorded, and the raw
  value is discarded.

## 6. WBS M7 item mapping

| Item | Where |
|---|---|
| 7.D0 design docs first | this document |
| 7.1 ask-gate broker | `agentpolicy/ask.py` |
| 7.2 `approve`/`deny` | `agentpolicy/cli/ask.py` |
| 7.3 redact-and-allow | `agentpolicy/redaction.py` (`redact_text`/`redact_output`) |
| 7.4 secrets-in-arguments | `agentpolicy/redaction.py` (`redact_argument_values`) |
| 7.T/7.C/7.L/7.CR/7.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [ask/redaction reference](../reference/ask-redaction.md) |
