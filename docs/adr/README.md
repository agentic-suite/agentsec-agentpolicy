# agentpolicy — Architecture Decision Records

ADRs record the **load-bearing decisions** and their rationale. Status: `proposed` → `accepted` → (rarely)
`superseded`. Superseding an ADR requires a new ADR that names it — decisions are never silently reversed.

| # | Decision | Status |
|---|---|---|
| [0001](0001-cedar-primary-policy-language.md) | Cedar is the primary policy language | accepted |
| [0002](0002-decide-only-never-enforce.md) | agentpolicy is a PDP; it never enforces | accepted |
| [0003](0003-five-outcome-decision-set.md) | The five-outcome decision set (allow/deny/ask/rate-limit/redact) | accepted |
| [0004](0004-no-ml-in-decision-path.md) | No ML in any decision path (NL drafting is authoring-time only) | accepted |
| [0005](0005-fail-closed-semantics.md) | Fail-closed semantics everywhere | accepted |
| [0006](0006-authzen-interop-binding.md) | AuthZEN Authorization API 1.0 as the interop binding | accepted |
| [0007](0007-agentwatch-event-schema.md) | Decisions emitted in the agentwatch security-event schema | accepted |
| [0008](0008-absorb-decision-model-replace-engine.md) | Absorb the predecessor's decision model, replace the engine | accepted |

Each ADR maps to decision records (DD-xx) in [PRD 11](../prd/11-decisions.md); ADRs carry the *why* in depth,
the PRD carries the requirement-side summary.
