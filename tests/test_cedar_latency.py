"""M2 ``2.5`` — the inline latency budget: sub-100 ms p99, plus cold-start.

The decision path is local and deterministic (no network/ML), so the sub-100 ms
p99 budget (PRD 13 / R8) is measured over a warm evaluator with a realistic
call, plus a cold-start (first-ever decision) bound.
"""

from __future__ import annotations

import statistics
import time

from agentpolicy.cedar import CedarEvaluator
from agentpolicy.types import NormalizedCall

_WARMUP = 50
_SAMPLES = 300


def _call() -> NormalizedCall:
    return NormalizedCall(
        tool="query_logs",
        tool_category="search",
        action="read",
        action_class="read",
        environment="staging",
        data_class="internal",
        agent_id="debug-bot",
        agent_class="general",
    )


def test_p99_under_100ms() -> None:
    evaluator = CedarEvaluator()
    call = _call()
    for _ in range(_WARMUP):
        evaluator.evaluate(call)

    samples_ms: list[float] = []
    for _ in range(_SAMPLES):
        start = time.perf_counter()
        evaluator.evaluate(call)
        samples_ms.append((time.perf_counter() - start) * 1000.0)

    p99 = statistics.quantiles(samples_ms, n=100)[98]
    assert p99 < 100.0, f"p99 was {p99:.2f} ms (budget 100 ms)"


def test_cold_start_budget() -> None:
    start = time.perf_counter()
    evaluator = CedarEvaluator()
    evaluator.evaluate(_call())
    cold_ms = (time.perf_counter() - start) * 1000.0
    # Generous cold-start bound (policy parse + first evaluation).
    assert cold_ms < 1000.0, f"cold start was {cold_ms:.2f} ms"
