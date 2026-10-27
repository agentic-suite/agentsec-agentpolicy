# EU AI Act Mapping

The **EU AI Act** imposes obligations on high-risk AI systems that trickle down to tooling vendors. agentpolicy
maps most directly to three articles — **Art. 9 (risk management)**, **Art. 12 (record-keeping/logging)**, and
**Art. 14 (human oversight)** — which are exactly the areas a deterministic policy + audit layer serves.

> Timeline still evolving; this is an **awareness mapping** for deployers, not legal advice or a conformity claim.

## Article mapping

| Article | Obligation | agentpolicy control |
|---|---|---|
| **Art. 9 — Risk management** | Establish a risk-management system across the lifecycle | The contextual decision model + the five outcomes + blast-radius budgets actively bound risk ([PRD 18](../prd/18-blast-radius-budgets.md)) |
| **Art. 12 — Record-keeping** | Automatic logging of events over the system's lifetime | The **hash-chained audit log** + decision events in the agentwatch schema ([PRD 17](../prd/17-explain-decision-and-evidence.md)) |
| **Art. 13 — Transparency** | Enable deployers to interpret outputs | The `explain-decision` contract (clause, factors, suggested change) |
| **Art. 14 — Human oversight** | Enable human oversight of high-risk systems | The **mandatory human-gate class** (`ask`) for irreversible actions; action-identity-bound approvals ([PRD 04](../prd/04-users-and-cujs.md) CUJ-10) |
| **Art. 15 — Accuracy, robustness, cybersecurity** | Appropriate levels of accuracy/robustness | Determinism, fail-closed semantics, the adversarial suite (R8, R26) |
| **Art. 72 — Post-market monitoring** | Monitor after deployment | Shadow mode + the decision event stream feeding agentwatch/agentcomply |

## Why logging is the strongest mapping

Art. 12's "automatic recording of events" is precisely what agentpolicy produces: every decision is a
**timestamped, hash-chained, policy-versioned** record, exportable and **offline-verifiable**
([PRD 17](../prd/17-explain-decision-and-evidence.md)). For an auditor, the chain proves the log is unedited.

## Deployer note

agentpolicy is a **control**, not a conformity assessment. A high-risk-system deployer uses agentpolicy to
satisfy parts of Art. 9/12/14; the conformity assessment itself (technical documentation, CE marking) remains the
deployer's responsibility. See [PRD 20](../prd/20-standards-and-claims.md) §G for the honesty rule.
