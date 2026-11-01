"""M23 — untrusted-pack sandbox & cost controls.

WBS M23: ``23.3`` sandbox · ``23.4`` cost controls. R6 (PRD 06) / R8.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentpolicy.cost import CostExceeded, CostGovernor
from agentpolicy.sandbox import (
    SandboxError,
    SandboxPolicy,
    authorize_pack,
    run_pack_sandboxed,
    sanitized_env,
)

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/code-freeze"


class TestSandbox:
    def test_sanitized_env_strips_secrets(self) -> None:
        env = {
            "PATH": "/usr/bin",
            "HOME": "/root",
            "AWS_SECRET_ACCESS_KEY": "x",
            "OPENAI_API_KEY": "y",
            "DB_PASSWORD": "z",
        }
        clean = sanitized_env(env)
        assert clean["PATH"] == "/usr/bin"
        assert clean["HOME"] == "/root"
        assert "AWS_SECRET_ACCESS_KEY" not in clean
        assert "OPENAI_API_KEY" not in clean
        assert "DB_PASSWORD" not in clean

    def test_allow_keeps_a_named_key(self) -> None:
        clean = sanitized_env({"API_KEY": "x", "PATH": "/bin"}, allow=("API_KEY",))
        assert clean["API_KEY"] == "x"

    def test_authorize_trust_levels(self) -> None:
        untrusted = SimpleNamespace(trust="untrusted", name="p")
        with pytest.raises(SandboxError, match="trust"):
            authorize_pack(untrusted, SandboxPolicy(required_trust="launch"))
        authorize_pack(
            SimpleNamespace(trust="launch", name="p"), SandboxPolicy(required_trust="launch")
        )

    def test_network_none_refuses_untrusted(self) -> None:
        community = SimpleNamespace(trust="community", name="p")
        with pytest.raises(SandboxError, match="network"):
            authorize_pack(community, SandboxPolicy(required_trust="community", network=True))

    def test_run_pack_sandboxed_emits_an_audit_event(self) -> None:
        results, events = run_pack_sandboxed(
            PACK, policy=SandboxPolicy(required_trust="launch")
        )
        assert results and all(r.passed for r in results)
        assert events and events[0]["kind"] == "pack_sandbox"
        assert "env" not in events[0]  # no env leaked into the audit event


class TestCostGovernor:
    def test_charge_over_ceiling_raises(self) -> None:
        governor = CostGovernor(max_cost=1.0)
        governor.charge(0.5)
        governor.charge(0.4)
        with pytest.raises(CostExceeded, match="ceiling"):
            governor.charge(0.2)
        assert governor.report()["spent"] == pytest.approx(0.9)

    def test_no_ceiling_never_raises(self) -> None:
        governor = CostGovernor()
        governor.charge(10_000.0)
        assert governor.report()["max_cost"] is None


class TestBacktestCost:
    def _files(self, tmp_path: Path) -> tuple[str, str]:
        hist = tmp_path / "history.jsonl"
        hist.write_text(
            json.dumps({
                "event_id": "evt_1",
                "action": {"verb": "write", "tool": "deploy_service"},
                "resource": {"environment": "staging", "data_class": "internal"},
                "principal": {"agent_id": "bot"},
                "timestamp": "2026-10-20T00:00:00+00:00",
            }),
            encoding="utf-8",
        )
        cand = tmp_path / "candidate.yaml"
        cand.write_text('version: "1.0.0"\nposture: balanced\n', encoding="utf-8")
        return str(hist), str(cand)

    def test_backtest_aborts_over_the_ceiling(self, tmp_path: Path) -> None:
        from agentpolicy.backtest import backtest
        from agentpolicy.policy.loader import load_policy

        hist, cand = self._files(tmp_path)
        from agentpolicy.backtest import load_history

        report = backtest(load_history(hist), load_policy(cand), max_cost=0.0)
        assert report.aborted is True
        assert report.abort_reason
