# Self-attack pack & allow-justification — reference (v0.1.0)

WBS M22 · CUJ-32 / CUJ-33 · R46 / R47. Design:
[self-attack-and-allow-justification.md](../design/self-attack-and-allow-justification.md).

## Self-attack pack (`22.1`, `22.2`)

```sh
agentpolicy self-attack check --pack packs/self-attack   # a miss exits 1
```

`packs/self-attack/` is a **normal pack** that attacks agentpolicy's own decision surface — `tamper`, `bypass`,
`replay`, `budget_split`, `audit_truncation`, `event_forgery` — dogfoodable by anyone. It runs through the same
pack format (`pack validate`, `pack test`, `drill check`). A fixture whose expected block is no longer produced
is a **miss** and **blocks the release** (`agentpolicy self-attack check` exits 1); the result is published
with the release notes, misses included. A Makefile `self-attack` target and a CI job run it every release.

## Allow-justification (`22.3`)

Every decision names its **matched rule** — allows included:

```python
decision.matched_rule     # "rule[3]" when an explicit rule decided it, else None
decision.clause           # matched_rule or reason_code — never empty
decision.policy_version   # the governing policy version
```

A **band-mapped** decision has `matched_rule=None` and its `clause` is the reason-code class, so no decision is
ever justification-less. The **audit entry** (`AuditEntry.matched_rule`) and its `policy_version` therefore
record the permitting rule for allows, exactly as for denies. The approval-analytics report also flags
**always-allowed** patterns (`ApprovalAnalytics.always_allowed_patterns`) — the allow-side mirror of the
rubber-stamp detector.
