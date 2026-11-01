#!/usr/bin/env python3
"""Benchmark the OMLX models for the field-test live sweep — pick the best fit.

The live framework sweep (``scripts/run_field_agents.py``) drives a real agent
whose only job is to emit a **tool call** for a scenario tool (``scn_<id>``). The
best field-test LLM is therefore the one that (a) reliably returns a ``tool_call``
and (b) does so fast. This sends N field-test-shaped trials (``tools=[scn_…]``,
``tool_choice=auto``) per model and prints tool-call reliability + latency + tps.

Usage::

    python3 scripts/fieldtest/omlx_bench.py                 # all models, 3 trials
    python3 scripts/fieldtest/omlx_bench.py --trials 5
    python3 scripts/fieldtest/omlx_bench.py --models Qwen3-4B-Instruct-2507-4bit
    python3 scripts/fieldtest/omlx_bench.py --endpoint http://127.0.0.1:8000/v1

Env: FT_LLM_HOST_URL (default http://127.0.0.1:8000), FT_LLM_MODEL.

Findings (2026-11-01, this box) — see docs/field-test/v0.1.0/FIELD_TEST_PLAN.md §4:
``Qwen3-4B-Instruct-2507-4bit`` is the best fit (~1.0 s p50, 3/3 tool calls);
``Llama-3.2-3B-Instruct-4bit`` never emitted a tool call (disqualified);
``Qwen3-8B-4bit`` was ~27 s (too slow).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.request

DEFAULT_HOST = os.environ.get("FT_LLM_HOST_URL", "http://127.0.0.1:8000")
DEFAULT_MODEL = os.environ.get("FT_LLM_MODEL", "Qwen3-4B-Instruct-2507-4bit")

# A field-test-shaped tool + imperative prompt (mirrors run_field_agents._prompt_for).
_TOOL = {
    "type": "function",
    "function": {
        "name": "scn_decision-allow-01",
        "description": "Run the field-test scenario decision-allow-01.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "reasoning or args"}},
            "required": [],
        },
    },
}
_PROMPT = (
    "In environment 'staging' with data_class 'internal', call ONLY the tool "
    "`scn_decision-allow-01` with valid arguments, then answer. Do not call any "
    "other tool. Do not skip."
)

#: Non-LLMs served by OMLX that must be skipped.
_SKIP = ("markitdown",)


def _models(base: str) -> list[str]:
    with urllib.request.urlopen(f"{base.rstrip('/')}/models", timeout=10) as r:
        data = json.loads(r.read().decode())
    return [m["id"] for m in data.get("data", [])]


def _one(base: str, model: str, timeout: float) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": _PROMPT}],
        "tools": [_TOOL],
        "tool_choice": "auto",
        "temperature": 0,
    }
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer omlx-test"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode())
    except Exception as exc:  # unreachable / timeout -> not a pass
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000, "tool": False,
                "err": f"{type(exc).__name__}"}
    ms = (time.perf_counter() - t0) * 1000
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message", {})
    calls = msg.get("tool_calls") or []
    usage = body.get("usage") or {}
    return {
        "ok": True, "ms": ms, "tool": bool(calls),
        "name": calls[0]["function"]["name"] if calls else "",
        "finish": choice.get("finish_reason"),
        "ctok": usage.get("completion_tokens", 0),
        "clen": len(msg.get("content") or ""),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Benchmark OMLX models for the field-test live sweep.")
    p.add_argument("--endpoint", default=f"{DEFAULT_HOST.rstrip('/')}/v1")
    p.add_argument("--trials", type=int, default=3)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--models", default="", help="comma-separated ids (default: all served)")
    args = p.parse_args(argv)

    if args.models:
        names = [m.strip() for m in args.models.split(",") if m.strip()]
    else:
        names = [m for m in _models(args.endpoint) if not any(s in m.lower() for s in _SKIP)]
    if not names:
        print("omlx-bench: no models to test", file=sys.stderr)
        return 1

    print(f"omlx-bench: {len(names)} model(s) x {args.trials} trial(s) @ {args.endpoint}")
    print(f"{'model':40} {'tool':>7} {'p50 ms':>8} {'min ms':>8} {'tps':>6} {'finish'}")
    print("-" * 84)
    verdict: list[tuple[float, str, int, int]] = []
    for model in names:
        rows = [_one(args.endpoint, model, args.timeout) for _ in range(args.trials)]
        oks = [r for r in rows if r["ok"]]
        tools = sum(1 for r in rows if r.get("tool"))
        p50 = statistics.median([r["ms"] for r in oks]) if oks else float("nan")
        mn = min((r["ms"] for r in oks), default=float("nan"))
        ms = statistics.mean([r["ms"] for r in oks]) if oks else 0.0
        ctok = statistics.mean([r["ctok"] for r in oks]) if oks else 0.0
        tps = f"{ctok / (ms / 1000):.1f}" if ms else "?"
        fin = (
            ",".join(sorted({str(r.get("finish")) for r in oks}))
            if oks
            else rows[0].get("err", "")
        )
        print(f"{model:40} {tools:>3}/{args.trials} {p50:>8.0f} {mn:>8.0f} {tps:>6} {fin}")
        verdict.append((p50, model, tools, args.trials))

    eligible = [v for v in verdict if v[2] == v[3]]  # all trials returned a tool call
    print()
    if not eligible:
        print(
            "omlx-bench: no model reliably emitted a tool call - do not use any "
            "for the live sweep.",
            file=sys.stderr,
        )
        return 1
    best = min(eligible, key=lambda v: v[0])
    print(
        f"omlx-bench: best fit = {best[1]} "
        f"(p50 {best[0]:.0f} ms, {best[2]}/{best[3]} tool calls)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
