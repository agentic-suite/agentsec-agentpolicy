"""M12 — session state, blast-radius budgets, rate limits, agenthalt.

WBS M12: ``12.1`` session state · ``12.2`` budgets · ``12.3`` rate/burst ·
``12.4`` agenthalt. CUJ-12, CUJ-18 (R9, R17, R23).
"""

from __future__ import annotations

from pathlib import Path

from agentpolicy.agenthalt import HaltController
from agentpolicy.audit.logger import AuditLogger
from agentpolicy.audit.sinks.jsonl import JsonlSink
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy
from agentpolicy.server.server_core import ServerCore
from agentpolicy.server.session_store import SessionStore


def _core(tmp_path: Path, halt: HaltController | None = None) -> ServerCore:
    return ServerCore(
        Engine(default_policy("balanced")), SessionStore(),
        AuditLogger(JsonlSink(tmp_path / "audit.jsonl")), halt,
    )


class TestSessionUsage:
    def test_record_usage_accumulates(self) -> None:
        store = SessionStore()
        store.get_or_create("s")
        store.record_usage("s", {"files": 2.0})
        store.record_usage("s", {"files": 3.0, "spend": 1.5})
        assert store.get("s").usage == {"files": 5.0, "spend": 1.5}  # type: ignore[union-attr]

    def test_exceeds_budgets_by_dimension(self) -> None:
        store = SessionStore()
        store.get_or_create("s", budgets={"files": 4, "spend": 5})
        store.record_usage("s", {"files": 5})
        assert store.exceeds_budgets("s")[0] is True
        assert store.exceeds_budgets("s")[1] is not None

    def test_budget_state_shape(self) -> None:
        store = SessionStore()
        store.get_or_create("s", budgets={"files": 4})
        store.record_usage("s", {"files": 6})
        state = store.budget_state("s")
        assert state["budgets"] == {"files": 4}
        assert state["usage"] == {"files": 6}
        assert state["over"] == ["files"]

    def test_unknown_session_is_empty(self) -> None:
        store = SessionStore()
        assert store.budget_state("nope") == {"budgets": {}, "usage": {}, "over": []}
        assert store.exceeds_budgets("nope") == (False, None)


class TestRateLimit:
    def test_rate_allow_throttles_and_returns_retry_after(self) -> None:
        store = SessionStore()
        store.get_or_create("s", rate_limit=1.0, burst_limit=1)
        allowed, retry = store.rate_allow("s")
        assert allowed is True and retry == 0
        blocked, retry = store.rate_allow("s")
        assert blocked is False and retry >= 1

    def test_no_rate_limit_always_allows(self) -> None:
        store = SessionStore()
        store.get_or_create("s")
        assert store.rate_allow("s") == (True, 0)


class TestAgentHalt:
    def test_halt_fires_on_over_budget(self) -> None:
        fired: list = []
        controller = HaltController(on_halt=fired.append)
        event = controller.maybe_halt("s", {"over": ["files"]})
        assert event is not None
        assert event.to_dict()["kind"] == "session_halt"
        assert "files" in event.reason
        assert fired == [event]

    def test_no_halt_when_within_budget(self) -> None:
        assert HaltController().maybe_halt("s", {"over": []}) is None

    def test_halt_callback_failure_is_swallowed(self) -> None:
        controller = HaltController(on_halt=lambda _e: (_ for _ in ()).throw(RuntimeError("x")))
        assert controller.maybe_halt("s", {"over": ["files"]}) is not None


class TestServerBudgetEnforcement:
    def _call(self, core: ServerCore, session: str, **kwargs) -> dict:
        return core.evaluate(
            "query_logs", "read", "staging", "internal", "bot1",
            session_id=session, **kwargs,
        )

    def test_budget_exhaustion_is_a_rate_limit_with_halt(self, tmp_path: Path) -> None:
        halt = HaltController()
        core = _core(tmp_path, halt)
        result = self._call(core, "s1", budgets={"files": 1}, usage={"files": 5})
        assert result["decision"] == "rate-limit"
        assert result["reason_code"] == "budget_exhausted"
        assert result["retry_after"] == 60
        assert result["halt"]["kind"] == "session_halt"
        assert halt.events

    def test_rate_limit_enforcement(self, tmp_path: Path) -> None:
        core = _core(tmp_path)
        first = self._call(core, "s2", rate_limit=1.0, burst_limit=1)
        assert first["decision"] == "allow"
        second = self._call(core, "s2")
        assert second["decision"] == "rate-limit"
        assert second["reason_code"] == "rate_limited"
        assert second["retry_after"] >= 1

    def test_budget_state_on_every_decision(self, tmp_path: Path) -> None:
        core = _core(tmp_path)
        result = self._call(core, "s3", budgets={"requests": 10})
        assert result["decision"] == "allow"
        assert result["budget_state"]["budgets"] == {"requests": 10}
        assert result["budget_state"]["usage"]["requests"] == 1

    def test_counting_cannot_be_evaded_by_splitting(self, tmp_path: Path) -> None:
        # Cumulative counting is per session, not per call: many calls cross one cap.
        core = _core(tmp_path)
        for _ in range(3):
            self._call(core, "sess-a", budgets={"calls": 2})
        result = self._call(core, "sess-a", budgets={"calls": 2})
        assert result["reason_code"] == "budget_exhausted"

    def test_sessions_are_independent(self, tmp_path: Path) -> None:
        core = _core(tmp_path)
        self._call(core, "a", budgets={"calls": 1})
        self._call(core, "a", budgets={"calls": 1})
        other = self._call(core, "b", budgets={"calls": 1})
        assert other["decision"] == "allow"

    def test_consent_still_escalates(self, tmp_path: Path) -> None:
        core = _core(tmp_path)
        result = core.evaluate(
            "deploy_service", "write", "production", "internal", "bot1",
            session_id="s4", consent_scopes=[{"tool": "query_logs", "env": "*", "data_class": "*"}],
        )
        assert result["decision"] == "escalate"
        assert result["reason_code"] == "scope_boundary"
