# AgentPolicy v0.1.0 — First-Run Evidence

> M25 25.2 (issue #269). Measured on this box with a clean-venv `pip install`
> of the release wheel; the decision path is deterministic (no ML/network).

## The journey

| Step | Command | Time | Exit |
|---|---|---|---|
| install | `pip install agentsec_agentpolicy-0.1.0-py3-none-any.whl` (fresh venv) | 0.05s | 0 |
| scaffold | `agentpolicy init -o agentpolicy.yaml` | 1.86s | 0 |
| first decision | `agentpolicy evaluate …` | 0.12s | 0 |

- **install → first correct decision:** **2.02s** — SLO **< 5 min**.
- **with `init` (scaffold + decide):** **1.98s** — SLO **< 2 min**.

## Verdict

****PASS**** (SLOs: install→decision < 5 min; init path < 2 min).

The recorded timings come from the release wheel's SHA256SUMS entry; reproduce
with `make release-dry-run` then `python3 scripts/release/first_run.py`.
