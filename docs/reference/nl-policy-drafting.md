# NL policy drafting — reference (v0.1.0)

WBS M19 · CUJ-27 · R42. Design: [nl-policy-drafting.md](../design/nl-policy-drafting.md).

Turn a sentence into a **candidate Cedar rule**. **Advisory and authoring-time only** — the runtime decision
path never calls a model, and a draft is never auto-pinned.

```sh
agentpolicy draft "deny deploy in production" --out candidate/
# writes candidate/rules.cedar + candidate/tests.yaml + candidate/metadata.yaml
```

```python
from agentpolicy.draft import draft, pin, run_draft

d = draft("deny deploy in production")     # compiles + passes its generated tests + lints clean
d.reviewed                                  # False — never auto-reviewed
all(r.passed for r in run_draft(d))         # True
pin(d, reviewed=True)                        # the only path to a reviewable artifact
```

A draft that **does not compile**, **fails its generated test**, or **lints dirty** is rejected
(`DraftError`). The generated `tests.yaml` uses the shipped pack format: a "fires" case (matching call → the
intent's outcome) and a "no-op" case (near-miss → the base-policy outcome, so a draft cannot silently broaden
the posture). `pin(draft)` without an explicit review raises `DraftError`.

**Boundary lock:** `agentpolicy/draft.py` is the only module that consults a model; `Engine`, the Cedar
evaluator, and every shipped pack contain no model call (asserted by the M19 boundary-lock test).
