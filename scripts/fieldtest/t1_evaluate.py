#!/usr/bin/env python3
"""FT-T1 evaluate helper — print the agentpolicy decision as one JSON line.

A thin, import-stable wrapper over the shipped loader + engine so the Tier-1
hooks (Claude Code PreToolUse, Codex, Gemini) can call the *shipped* decision
path from a shell hook and capture the decision as evidence. Never forks the
engine: it is exactly `load_policy(path)` + `Engine.evaluate(...)`, the same
call the `agentpolicy evaluate` CLI makes, minus argparse overhead in the
hot path of every tool call.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentpolicy.engine.engine import Engine
from agentpolicy.policy.loader import load_policy


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tool", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--env", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--session", default=None)
    p.add_argument("--policy", required=True)
    a = p.parse_args(argv)
    policy = load_policy(a.policy)
    decision = Engine(policy).evaluate(
        tool_name=a.tool, action=a.action, environment=a.env,
        data_class=a.data, agent_id=a.agent,
    )
    print(json.dumps(decision.to_dict()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

