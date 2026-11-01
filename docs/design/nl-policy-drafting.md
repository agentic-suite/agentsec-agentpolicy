# NL Policy Drafting — Design (M19, v0.1.0)

**BLUF:** M19 ships `agentpolicy draft` — turn a sentence into a **candidate Cedar rule** that must **compile,
pass its generated tests, and lint clean**, then **wait for human review**. It is **advisory only** and lives
**entirely outside the runtime decision path**: the deterministic evaluator never calls a model. This is the
design of record (`19.D0`); it delivers **CUJ-27** (R42).

> Status: **Done** — branch `feat-0.1.0`. Module: `agentpolicy/draft.py`, `cli/draft.py`.

---

## 1. The boundary lock (the load-bearing rule)

The **runtime decision path is untouched**: `Engine.evaluate`, the Cedar evaluator, and every shipped pack
contain **no** model call. `agentpolicy/draft.py` is the *only* module that consults a model, and it is never
imported by the decision path. The boundary is proven by a test (`19.3`) that spies on the model callable and
asserts no runtime evaluation invokes it. A draft is a **review artifact**, not a control.

## 2. The drafter (`19.1`)

`agentpolicy/draft.py`:

* `default_model(sentence) -> dict` — a **deterministic** intent parser (NL → intent) so drafting works offline
  and in tests. An intent names the `effect` (`forbid`/`permit`), the `verb`, and optional `environment` /
  `data_class` constraints drawn from the canonical taxonomy/environments.
* `draft_rule(sentence, *, model=default_model) -> Draft` — renders the intent to a Cedar `permit`/`forbid`
  clause with an `@id("draft-…")`, so it is a first-class rule that can later be pinned into a pack.
* `Draft` — `draft_id`, `sentence`, `rule_id`, `cedar`, `fixtures`, `reviewed` (default **False**).

The model is injectable (`model=`), so a real provider can be swapped in without changing the pipeline; the
default keeps the tool deterministic and network-free.

## 3. Generated tests (`19.2`)

`draft_rule` also emits `tests.yaml` fixtures in the **shipped pack format** (`pack_format`), so a draft is
validated exactly like any pack:

* a **"fires"** fixture (a call matching the intent) expecting the intent's outcome — `deny` for a `forbid`,
  `allow` for a `permit`; and
* a **"no-op"** fixture (a near-miss call) expecting the *base-policy* outcome, so a draft cannot silently
  broaden the posture.

`Draft.tests_yaml()` serialises the fixtures; `run_draft(draft)` compiles the rule (`BASE_POLICY + rule`) and
replays the fixtures through the Cedar core, returning `PackTestResult`s. **A draft that does not compile, or
whose generated test fails, is rejected** (`DraftError`) — it never reaches review.

## 4. Human-review gate (`19.3`)

A draft is **never auto-pinned**. `Draft.reviewed` is `False` on creation, and `pin(draft, reviewed=True)` is the
only path to a reviewable artifact: calling `pin` without an explicit review raises `DraftError`. The
`agentpolicy draft` CLI writes the candidate `rules.cedar` + `tests.yaml` (+ `metadata.yaml`) to a directory and
**stops** — a human reviews and pins it; the runtime is never changed by drafting.

## 5. WBS M19 item mapping

| Item | Where |
|---|---|
| 19.D0 design docs first | this document |
| 19.1 `agentpolicy draft` | `agentpolicy/draft.py`, `cli/draft.py` |
| 19.2 generated tests | `Draft.fixtures`, `tests_yaml()`, `run_draft` (pack format) |
| 19.3 human-review gate + boundary lock | `pin`, the boundary-lock test |
| 19.T/19.C/19.L/19.CR/19.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [NL-drafting reference](../reference/nl-policy-drafting.md) |
