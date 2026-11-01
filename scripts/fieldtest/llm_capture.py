#!/usr/bin/env python3
"""Make one real LLM call through the pinned OpenAI-compatible endpoint and
record the request/response pair (sanitized) as field-test evidence (must).

Writes ``<name>-request.json`` and ``<name>-response.json`` under ``--out`` with
secrets masked, so an LLM-required case has a durable, committable pair. The
harness's ``ft_assert_llm_capture`` requires a real 2xx pair and fails a case
that captured none.

Usage::

    python3 scripts/fieldtest/llm_capture.py --out DIR --name probe \\
        --base-url http://127.0.0.1:8000/v1 --model Qwen3-4B-Instruct-2507-4bit [--prompt "..."]

Exit non-zero if the endpoint is unreachable (never a fake pair).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

_SECRET = re.compile(r"sk-[A-Za-z0-9]{16,}|bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE)


def _sanitize(obj: object) -> object:
    if isinstance(obj, str):
        return _SECRET.sub("[REDACTED]", obj)
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in ("api_key", "authorization") else _sanitize(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True)
    p.add_argument("--name", default="probe")
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--prompt", default="Reply with the single word: ok")
    p.add_argument("--timeout", type=float, default=60.0)
    args = p.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "temperature": 0,
    }
    url = args.base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer omlx-test"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except Exception as exc:  # endpoint unreachable -> no fake pair
        print(f"llm-capture: endpoint {url} unreachable: {exc}", file=sys.stderr)
        return 1

    (out / f"{args.name}-request.json").write_text(
        json.dumps({"url": url, "body": _sanitize(payload)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        parsed = json.loads(body)
    except ValueError:
        parsed = body
    (out / f"{args.name}-response.json").write_text(
        json.dumps(
            {"status_code": status, "body": _sanitize(parsed)}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"llm-capture: {args.name} -> HTTP {status}; pair written to {out}")
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
