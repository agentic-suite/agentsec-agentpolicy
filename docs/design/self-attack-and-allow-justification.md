# Self-Attack Pack & Allow-Justification — Design (M22, v0.1.0)

**BLUF:** M22 turns agentpolicy's proof discipline on **itself**: a shipped `self-attack` pack drills the
decision surface (policy tamper, normalization bypass, ask replay, budget splitting, audit truncation, event
forgery) as a **normal pack** anyone can run, and a **release-cadence CI job** blocks the release on a miss.
And **allow-justification** makes **every** outcome — allows included — name its matched rule and policy
version. This is the design of record (`22.D0`); it delivers **CUJ-32** and **CUJ-33** (R46, R47).

> Status: **Done** — branch `feat-0.1.0`. Artifacts: `packs/self-attack/`, `agentpolicy/selfattack.py`,
> `cli/ci.py` (`self-attack check`), `types.Decision.matched_rule`, `approvals.analyze_approvals`.

---

## 1. The `self-attack` pack (`22.1`)

`packs/self-attack/` is a **normal rule pack** (`metadata.yaml` + `rules.cedar` + `tests.yaml`) — nothing
special-cased, so a third party can run it against *their* deployment. Its rule class blocks a call that
carries a self-attack marker in `context.self_attack`, one fixture per attack class:

| `context.self_attack` | attack class |
|---|---|
| `tamper` | policy tamper (mutate the pinned policy) |
| `bypass` | normalization / dispatcher bypass |
| `replay` | ask/escalation replay |
| `budget_split` | split a blast radius across sessions |
| `audit_truncation` | truncate the audit chain |
| `event_forgery` | forge an agentwatch event |

A benign fixture (no marker) must remain allowed, so the pack cannot pass by denying everything. The pack is
**dogfoodable**: `pack validate` / `pack test` / `drill check` all work on it unchanged.

## 2. Release-cadence CI job (`22.2`)

`agentpolicy/selfattack.py` replays the pack and reports each attack class as **blocked** or a **miss**.
`agentpolicy self-attack check [--pack packs/self-attack]` exits **1** on any miss — "a miss blocks the
release" — and the pack's result (misses included) is the claim published with the release. A Makefile target
and a CI job (`.github/workflows/ci.yml`) run it every release.

## 3. Allow-justification (`22.3`)

An auditor's first question is "who authorized this allow?". So every decision names its **matched rule**:

* `types.Decision` gains an additive `matched_rule: str | None` and a `clause` property
  (`matched_rule or reason_code`), mirroring the Cedar `Explanation.clause` — the same contract on both paths.
* `engine.decide` records the matched rule id (`rule[i]`) on the `Verdict`; `explain` carries it onto the
  `Decision`. A **band-mapped** decision (no explicit rule) has `matched_rule = None` and its clause is the
  reason-code class — so no decision is ever justification-less.
* The **audit entry** (M6) already reads `getattr(decision, "matched_rule", None)`, so allows now name the
  permitting rule + `policy_version` in the audit trail too — the allow-side counterpart of the deny contract.
* **Allow-side analytics:** `analyze_approvals` also flags **always-allowed** patterns (an allow clause that is
  permitted ~100% of the time over a corpus) — the R36 rubber-stamp detector's allow-side mirror.

## 4. WBS M22 item mapping

| Item | Where |
|---|---|
| 22.D0 design docs first | this document |
| 22.1 `self-attack` pack | `packs/self-attack/` |
| 22.2 release-cadence CI job | `agentpolicy/selfattack.py`, `cli/ci.py`, Makefile, `ci.yml` |
| 22.3 allow-justification | `types.Decision.matched_rule`/`clause`, `engine/decide.py`, `engine/explain.py`, `approvals.py` |
| 22.T/22.C/22.L/22.CR/22.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [self-attack/allow-justification reference](../reference/self-attack-and-allow-justification.md) |
