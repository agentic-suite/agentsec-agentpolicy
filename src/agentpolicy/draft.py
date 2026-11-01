"""NL policy drafting (WBS M19 ``19.1``-``19.3``, CUJ-27 / R42).

Turn a sentence into a **candidate Cedar rule** — **advisory only** and
**authoring-time only**. This module is the *only* place a model is consulted;
the runtime decision path (`Engine`, the Cedar evaluator, every shipped pack)
never imports it and never calls a model (the boundary lock).

A draft must **compile**, **pass its generated tests**, and **lint clean**, then
**wait for human review** — it is never auto-pinned.
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

import yaml

from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cedar.policy import BASE_POLICY
from agentpolicy.lint import lint_text
from agentpolicy.pack_format import PackTestResult

#: NL → intent. A model callable returns ``{effect, verb, environment, data_class}``.
Model = Callable[[str], dict[str, Any]]

_DENY_WORDS = ("deny", "block", "forbid", "disallow", "prevent", "stop")
_VERBS = frozenset(
    {"deploy", "write", "send", "transfer", "grant", "delete", "drop", "destroy",
     "read", "query", "revoke", "force_push", "purge", "approve"}
)
_ENVIRONMENTS = ("development", "staging", "production", "pre_prod")
_DATA_CLASSES = ("customer_pii", "restricted", "secret", "internal")

#: A representative known tool per call — the draft rule keys on the *verb* +
#: environment + data class, so the tool only has to canonicalize.
_FIXTURE_TOOL = "deploy_service"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def default_model(sentence: str) -> dict[str, Any]:
    """The default (deterministic, offline) NL → intent parser."""
    lowered = sentence.lower()
    effect = "forbid" if any(w in lowered for w in _DENY_WORDS) else "permit"
    verb = next(
        (v for v in sorted(_VERBS) if re.search(rf"\b{re.escape(v)}\b", lowered)), "write"
    )
    environment = next((e for e in _ENVIRONMENTS if e in lowered), None)
    data_class = next((d for d in _DATA_CLASSES if d in lowered), None)
    return {"effect": effect, "verb": verb, "environment": environment, "data_class": data_class}


@dataclass(frozen=True)
class Draft:
    """A candidate Cedar rule + its generated tests (never auto-reviewed)."""

    draft_id: str
    sentence: str
    rule_id: str
    effect: str
    cedar: str
    fixtures: tuple[dict[str, Any], ...]
    reviewed: bool = False

    def tests_yaml(self) -> str:
        """Serialise the generated fixtures as a ``tests.yaml`` document."""
        return yaml.safe_dump({"fixtures": [dict(f) for f in self.fixtures]}, sort_keys=False)

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "draft_id": self.draft_id,
            "sentence": self.sentence,
            "rule_id": self.rule_id,
            "effect": self.effect,
            "cedar": self.cedar,
            "fixtures": [dict(f) for f in self.fixtures],
            "reviewed": self.reviewed,
        }


class DraftError(Exception):
    """A draft that cannot compile, fails its own tests, lints dirty, or is unpinned."""


def _rule_id(intent: dict[str, Any]) -> str:
    parts = [str(intent["verb"])]
    if intent.get("environment"):
        parts.append(str(intent["environment"]))
    if intent.get("data_class"):
        parts.append(str(intent["data_class"]))
    return "draft-" + "-".join(_slug(p) for p in parts)


def _render_rule(rule_id: str, intent: dict[str, Any]) -> str:
    conditions = [f'context.verb == "{intent["verb"]}"']
    if intent.get("environment"):
        conditions.append(f'context.environment == "{intent["environment"]}"')
    if intent.get("data_class"):
        conditions.append(f'context.data_class == "{intent["data_class"]}"')
    when = " && ".join(conditions)
    return (
        f'@id("{rule_id}")\n'
        f'{intent["effect"]} (principal, action, resource)\n'
        f"when {{ {when} }};\n"
    )


def _call(verb: str, environment: str, data_class: str) -> Any:
    return canonicalize(
        tool=_FIXTURE_TOOL, action=verb, environment=environment, data_class=data_class,
        agent_id="draft-tester",
    )


def _fixtures(intent: dict[str, Any], rule_id: str) -> tuple[dict[str, Any], ...]:
    verb = str(intent["verb"])
    environment = str(intent.get("environment") or "production")
    data_class = str(intent.get("data_class") or "internal")
    expect = "deny" if intent["effect"] == "forbid" else "allow"
    fires = {
        "name": f"{rule_id}-fires", "tool": _FIXTURE_TOOL, "action": verb,
        "environment": environment, "data_class": data_class, "expect": expect,
    }
    # A near-miss call that must NOT be touched by the new rule.
    if intent.get("environment"):
        miss_env = "development" if environment != "development" else "production"
        miss_verb, miss_data = verb, data_class
    elif intent.get("data_class"):
        miss_env = environment
        miss_verb = verb
        miss_data = "internal" if data_class != "internal" else "restricted"
    else:
        miss_env, miss_data = environment, data_class
        miss_verb = "read" if verb != "read" else "write"
    base = CedarEvaluator(BASE_POLICY)
    miss = base.evaluate(_call(miss_verb, miss_env, miss_data))
    noop = {
        "name": f"{rule_id}-noop", "tool": _FIXTURE_TOOL, "action": miss_verb,
        "environment": miss_env, "data_class": miss_data, "expect": miss.decision,
    }
    return (fires, noop)


def run_draft(draft: Draft) -> list[PackTestResult]:
    """Compile a draft and replay its generated fixtures through the Cedar core."""
    evaluator = CedarEvaluator(BASE_POLICY + "\n" + draft.cedar)
    results: list[PackTestResult] = []
    for fixture in draft.fixtures:
        call = _call(
            str(fixture["action"]), str(fixture["environment"]), str(fixture["data_class"])
        )
        got = evaluator.evaluate(call).decision
        expected = str(fixture["expect"])
        results.append(
            PackTestResult(
                name=str(fixture["name"]), expected=expected, got=got, passed=got == expected
            )
        )
    return results


def lint_draft(draft: Draft) -> list[Any]:
    """Lint a draft's Cedar text (literal secret/PII scan); ``[]`` is clean."""
    return lint_text(draft.cedar)


def draft(sentence: str, *, model: Model | None = None) -> Draft:
    """Draft a candidate rule from *sentence* (compile + generated tests + lint).

    Raises:
        DraftError: the draft does not compile, fails its generated test, or lints dirty.
    """
    chosen = model or default_model
    intent = chosen(sentence)
    rule_id = _rule_id(intent)
    cedar = _render_rule(rule_id, intent)
    candidate = Draft(
        draft_id="drf_" + secrets.token_hex(8), sentence=sentence, rule_id=rule_id,
        effect=str(intent["effect"]), cedar=cedar, fixtures=(),
    )
    try:
        fixtures = _fixtures(intent, rule_id)
        candidate = replace(candidate, fixtures=fixtures)
        results = run_draft(candidate)
    except (ValueError, TypeError) as exc:
        raise DraftError(f"draft for {sentence!r} does not compile: {exc}") from exc
    failed = [r for r in results if not r.passed]
    if failed:
        raise DraftError(
            f"draft for {sentence!r} failed its generated test: "
            + "; ".join(f"{r.name} expected {r.expected} got {r.got}" for r in failed)
        )
    findings = [f for f in lint_draft(candidate) if getattr(f, "severity", "") == "error"]
    if findings:
        raise DraftError(f"draft for {sentence!r} lints dirty: {findings[0].message}")
    return candidate


def pin(draft_obj: Draft, *, reviewed: bool = False) -> Draft:
    """Pin a reviewed draft (the human-review gate).

    Raises:
        DraftError: the draft was not explicitly reviewed; a draft is never
            auto-pinned.
    """
    if not reviewed:
        raise DraftError("a draft must be human-reviewed before it can be pinned")
    return replace(draft_obj, reviewed=True)


__all__ = [
    "Draft",
    "DraftError",
    "Model",
    "default_model",
    "draft",
    "lint_draft",
    "pin",
    "run_draft",
]
