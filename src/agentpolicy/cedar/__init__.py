"""agentpolicy Cedar decision core (WBS M2 — the five-outcome PDP).

A deterministic Cedar PDP returning ``allow`` / ``deny`` / ``ask`` /
``rate-limit`` / ``redact``. See :mod:`agentpolicy.cedar.evaluator` (evaluation),
:mod:`agentpolicy.cedar.shaper` (outcome shaping), :mod:`agentpolicy.cedar.gates`
(the mandatory human-gate class), and :mod:`agentpolicy.cedar.models` (the
PRD 15 decision model).
"""

from __future__ import annotations

from agentpolicy.cedar import gates, policy
from agentpolicy.cedar.evaluator import CedarEvaluator
from agentpolicy.cedar.models import OUTCOMES, Decision, Explanation, Factor, Outcome
from agentpolicy.cedar.shaper import ShaperContext, shape

__all__ = [
    "OUTCOMES",
    "CedarEvaluator",
    "Decision",
    "Explanation",
    "Factor",
    "Outcome",
    "ShaperContext",
    "gates",
    "policy",
    "shape",
]
