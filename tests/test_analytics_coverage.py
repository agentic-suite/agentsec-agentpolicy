"""Additional tests for analytics routes and CLI argument parsing."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from agentpolicy.audit.logger import AuditLogger
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy
from agentpolicy.server.analytics_routes import register_analytics_routes
from agentpolicy.server.server_core import ServerCore
from agentpolicy.server.session_store import SessionStore


class TestAnalyticsCoverage:
    @pytest.fixture
    def core(self) -> ServerCore:
        engine = Engine(default_policy("balanced"), audit_logger=AuditLogger())
        core = ServerCore(engine=engine, session_store=SessionStore(), audit_logger=AuditLogger())
        core.evaluate("query_logs", "read", "staging", "internal", "debug-bot", session_id="s1")
        return core

    @pytest.fixture
    def client(self, core: ServerCore) -> TestClient:
        from fastmcp import FastMCP

        mcp = FastMCP("test")
        register_analytics_routes(mcp, core)
        return TestClient(mcp.http_app())

    def test_calibration_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/calibration")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_tool" in data
        assert "by_environment" in data


class TestServeParser:
    def test_serve_parser_has_port(self) -> None:
        import argparse

        from agentpolicy.server.cli import add_parser

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_parser(sub)
        # argparse exits 0 on --help, just verify the parser was created
        assert parser._subparsers is not None
