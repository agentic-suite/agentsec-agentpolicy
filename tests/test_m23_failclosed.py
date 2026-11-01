"""M23 — fail-closed fault injection across every engine stage (R8).

WBS M23: ``23.2`` fail-closed fault injection. A failure injected at any stage
yields a deny with a reason code; the injection loop never aborts.
"""

from __future__ import annotations

import pytest

import agentpolicy.engine.engine as engine_mod
from agentpolicy.engine.engine import Engine
from agentpolicy.errors import DENY_ENGINE_UNAVAILABLE, AgentPolicyError
from agentpolicy.faultinject import InjectedFault, fault_hook
from agentpolicy.policy.models import default_policy

#: The engine's module-level stage callables — one fault point each.
_STAGES = (
    "normalize",
    "scoping_violation",
    "check_arguments",
    "exfil_violation",
    "score",
    "decide",
    "explain",
)


def _evaluate() -> object:
    return Engine(default_policy("balanced")).evaluate(
        tool_name="query_logs", action="read", environment="staging",
        data_class="internal", agent_id="debug-bot",
    )


def test_injected_fault_is_an_agentpolicy_error() -> None:
    fault = InjectedFault(DENY_ENGINE_UNAVAILABLE)
    assert isinstance(fault, AgentPolicyError)
    assert fault.reason_code == DENY_ENGINE_UNAVAILABLE


@pytest.mark.parametrize("stage", _STAGES)
def test_stage_fault_fails_closed(monkeypatch: pytest.MonkeyPatch, stage: str) -> None:
    monkeypatch.setattr(engine_mod, stage, fault_hook(DENY_ENGINE_UNAVAILABLE))
    decision = _evaluate()
    assert decision.decision == "deny"  # type: ignore[attr-defined]
    assert decision.reason_code == DENY_ENGINE_UNAVAILABLE  # type: ignore[attr-defined]


def test_injection_loop_never_aborts() -> None:
    # Every stage is faulted in turn; none of them may raise out of evaluate().
    for stage in _STAGES:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(engine_mod, stage, fault_hook(DENY_ENGINE_UNAVAILABLE))
            decision = _evaluate()
        assert decision.decision == "deny"  # type: ignore[attr-defined]
