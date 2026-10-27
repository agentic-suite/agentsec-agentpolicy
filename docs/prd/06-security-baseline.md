# PRD 06 — Security Baseline

**BLUF:** agentpolicy is the ecosystem's **single source of authorization truth** — if it is wrong or
compromised, every enforcer above it is wrong. Its assets are the policy, the decision it returns, and the
trust in its explanations. Its **own attack surface** — policy tampering, decision forging, ask replay, budget
evasion, tool-name obfuscation — is not a footnote but the **adversarial sub-matrix** of the field test
(CUJ-11). Running **untrusted community rule packs** inherits the predecessor's sandbox / trust-policy / audit
model.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Assets

| Asset | Why it matters |
|---|---|
| Policy (Cedar files, rule packs) | Tampering changes what "allowed" means for the whole stack |
| The decision + explanation | The trust artifact; a wrong decision is a silent breach |
| The decision log / audit | The compliance and incident-response record |
| Ask-gate approvals | A forged/replayed approval authorizes an irreversible action |
| Budget/session state | Evading budgets defeats blast-radius limits |
| The evaluator itself | If compromised, the attacker owns authorization |

## Controls

- **Determinism + versioning** (R7): every decision records the `policy_version` + policy hash; a policy change
  is a git event, and a change without review is flagged.
- **Fail-closed everywhere** (R8): engine unavailable, malformed policy, OPA unreachable, timeout, unknown
  action → `deny` with a distinct `reason_code` (CUJ-9).
- **Tamper-evident audit** (F17): an append-only hash chain over the decision log; verification proves the log
  is unedited.
- **Action-identity binding** (R18): an ask approval is bound to `(tool, args hash)` so it cannot be replayed
  for a different call.
- **No secrets in decisions or logs**: secrets referenced by name only; outputs are redacted with receipts
  (R20) — the raw value is never persisted.
- **Policy reviewed like code** (R7): two-party review; signed rule packs on release.

## agentpolicy's own attack surface (the adversarial sub-matrix)

Operationalized directly from the ecosystem's own threat model — the surface/threat/defense table:

| Surface | Threat | Defense (test) |
|---|---|---|
| Policy files / rule packs | Tamper a rule so a deny becomes an allow | Policy hash in every decision; tamper → fail-closed; signed packs |
| The evaluator | Craft an input that the normalizer and the evaluator disagree on | One canonical action shape for both; adversarial normalization suite (CUJ-11) |
| Tool names / arguments | Obfuscation (`"deploy_service "`, Unicode, case) or dispatcher smuggling | Normalize before matching; unknown normalized name → deny (R24) |
| Ask approvals | Replay an approval for a different action | Action-identity binding; expiry; timeout=deny (R18) |
| Budgets | Split an action to evade a per-session ceiling | Cumulative counters on the session, not per call (R9) |
| The event stream | Inject a forged decision event into telemetry | Decisions are signed/hash-bound to the audit chain; telemetry treated as untrusted input |
| The audit log | Edit a published decision | Hash chain; verification command proves unedited history (F17) |
| The LLM advisor (if enabled) | Steer the explanation to widen scope | The advisor is **non-authoritative** and can only narrow/escalate, never widen (DD-07) |

Anti-tamper principles (from the ecosystem own-threat-model): the decision lives **outside** the model's control
plane; **fail-closed** on integrity failure; **assume the enforcer is compromised** and still return the right
decision; **separation of duties** between what holds secrets, decides, and observes.

This table is **operationalized as a shipped pack** — the `self-attack` pack (R46) runs against the deployed
PDP every release cycle, misses published, a hit release-blocking ([PRD 23](23-enterprise-adoption-and-governance-hardening.md)).

## Running untrusted rule packs (absorbed from the predecessor)

Community packs contain **executable policy + validators**, so they get the predecessor's security model:

- **Schema validation** — strict pack schema; identifiers used in paths match `^[a-zA-Z0-9_-]+$` (closes the
  predecessor's path-traversal gap).
- **Trust levels** — `built-in` / `local` / `external`; external packs are limited to declarative Cedar +
  pure-function validators (no arbitrary code) and are sandboxed.
- **Sandbox mode** — strip environment variables (allowlist `PATH`, `HOME`, `TMPDIR`, `USER`, `AGENTPOLICY_*`),
  filesystem isolation, optional Docker `--network none` for validators.
- **Audit trail** — per-run append-only log of policy/trust decisions.
- **Secret sanitization** — deep redaction in artifacts and logs.

## Fail-closed contract (the safety spine)

Any exception, unknown rule input, or disabled engine → `deny` (configurable to `ask`, never to `allow` by
default). Determinism: same input + policy → same decision, always. No external network dependency in the hot
path (the LLM advisor is off by default). This contract is itself a CI test.

## Disclosure

Security problems are reported privately — see [SECURITY.md](../../SECURITY.md) (and the
[organization security policy](https://github.com/agentic-suite/.github/blob/main/SECURITY.md)). Do not open
public issues for security problems. The adversarial sub-matrix is the *sanctioned* way to attack agentpolicy;
unsanctioned testing follows the org disclosure process.
