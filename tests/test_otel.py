"""Tests for OTel tracing on Engine.evaluate()."""

from __future__ import annotations

import pytest

from agentpolicy.engine.engine import Engine
from agentpolicy.engine.otel import setup_tracing, trace_evaluate
from agentpolicy.policy.models import default_policy


class TestOTelTracing:
    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        setup_tracing(service_name="test-agentpolicy", console_export=False)

    def test_traced_evaluate_returns_same_decision(self) -> None:
        engine = Engine(default_policy("balanced"))
        original = engine.evaluate(
            tool_name="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="debug-bot",
        )
        traced_engine = Engine(default_policy("balanced"))
        traced = trace_evaluate(traced_engine)
        result = traced(
            tool_name="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="debug-bot",
        )
        assert result.decision == original.decision
        assert result.reason_code == original.reason_code

    def test_traced_deny_returns_deny(self) -> None:
        engine = Engine(default_policy("balanced"))
        traced = trace_evaluate(engine)
        result = traced(
            tool_name="drop_database",
            action="delete",
            environment="production",
            data_class="customer_pii",
            agent_id="bad-bot",
        )
        assert result.decision == "deny"

    def test_traced_span_attributes(self) -> None:
        from opentelemetry.sdk.trace import TracerProvider

        provider = TracerProvider()
        engine = Engine(default_policy("balanced"))
        traced = trace_evaluate(engine, tracer_provider=provider)
        result = traced(
            tool_name="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="debug-bot",
        )
        assert result.decision == "allow"
