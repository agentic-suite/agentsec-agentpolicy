"""M3 — canonical action, normalization, dispatcher safety, taxonomy, contextual matrix.

WBS M3: ``3.1`` canonical action · ``3.2`` tool-name normalization · ``3.3``
dispatcher-bypass safety · ``3.4`` action taxonomy · ``3.5`` contextual model.
Enables CUJ-1/CUJ-11.
"""

from __future__ import annotations

import pytest

from agentpolicy.canonical import (
    canonicalize,
    canonicalize_command,
    taxonomy_view,
    to_cedar_request,
)
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.errors import UnknownToolError
from agentpolicy.taxonomy import DOMAINS, action_class_for, domain_for, is_known_tool


class TestCanonicalAction:
    def test_resolves_taxonomy(self) -> None:
        call = canonicalize(
            tool="drop_database",
            action="delete",
            environment="production",
            data_class="customer_pii",
            agent_id="release-bot",
        )
        assert (call.tool, call.tool_category, call.action_class) == (
            "drop_database",
            "db",
            "delete",
        )

    def test_unknown_tool_raises(self) -> None:
        with pytest.raises(UnknownToolError):
            canonicalize(
                tool="definitely_not_a_tool",
                action="read",
                environment="staging",
                data_class="internal",
                agent_id="x",
            )

    def test_tool_name_folding(self) -> None:
        call = canonicalize(
            tool="Query_Logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="x",
        )
        assert call.tool == "query_logs"

    def test_to_cedar_request_shape(self) -> None:
        call = canonicalize(
            tool="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="debug-bot",
        )
        request = to_cedar_request(call)
        assert set(request) == {"principal", "action", "resource", "context"}
        assert request["context"]["environment"] == "staging"
        assert request["principal"]["id"] == "debug-bot"

    def test_taxonomy_view(self) -> None:
        call = canonicalize(
            tool="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="x",
        )
        view = taxonomy_view(call)
        assert view["domain"] == "search" and view["known_tool"] is True


class TestDispatcherSafety:
    def test_smuggled_force_push_canonicalizes(self) -> None:
        call = canonicalize_command(
            "git push --force",
            kind="git",
            environment="production",
            data_class="internal",
            agent_id="release-bot",
        )
        assert call.action == "force_push"
        assert call.action_class == "delete"

    def test_unsupported_kind_raises(self) -> None:
        with pytest.raises(ValueError, match="unsupported dispatch kind"):
            canonicalize_command(
                "x", kind="nope", environment="staging", data_class="internal", agent_id="x"
            )

    def test_smuggled_action_is_denied_by_cedar(self) -> None:
        evaluator = CedarEvaluator()
        call = canonicalize_command(
            "git push --force",
            kind="git",
            environment="production",
            data_class="internal",
            agent_id="release-bot",
        )
        assert evaluator.evaluate(call).decision == "deny"


class TestTaxonomy:
    def test_thirteen_domains(self) -> None:
        assert len(DOMAINS) == 13

    def test_domain_and_action_class(self) -> None:
        assert domain_for("drop_database") == "db"
        assert action_class_for("delete") == "delete"

    def test_unknown_tool_not_known(self) -> None:
        assert is_known_tool("made_up_tool") is False


class TestContextualMatrix:
    def _decision(self, environment: str, data_class: str) -> str:
        evaluator = CedarEvaluator()
        call = canonicalize(
            tool="query_logs",
            action="read",
            environment=environment,
            data_class=data_class,
            agent_id="bot",
        )
        return evaluator.evaluate(call).decision

    def test_same_call_scores_differently_across_context(self) -> None:
        assert self._decision("staging", "internal") == "allow"
        assert self._decision("production", "internal") == "deny"
        assert self._decision("production", "restricted") == "redact"
