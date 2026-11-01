"""``agentpolicy backtest`` — replay a history window against a candidate policy (WBS M20).

Read-only and advisory: the flip set is attached to the PR step summary with
``--ci`` and never fails the build.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from agentpolicy.backtest import backtest, load_history
from agentpolicy.cli.errors import CliError
from agentpolicy.policy.loader import load_policy


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy backtest`` subcommand parser."""
    parser = subparsers.add_parser(
        "backtest", help="replay recorded history against a candidate policy (advisory)",
        description="Diff a candidate policy against a window of recorded decisions.",
    )
    parser.add_argument("--history", required=True, help="JSONL window of agentwatch events")
    parser.add_argument("--candidate", required=True, help="the candidate policy file")
    parser.add_argument("--baseline", default=None, help="the baseline policy (default: balanced)")
    parser.add_argument("--ci", action="store_true", help="attach the diff to $GITHUB_STEP_SUMMARY")
    parser.add_argument("--json", action="store_true")
    parser.set_defaults(func=_backtest)


def _backtest(args: argparse.Namespace) -> int:
    try:
        candidate = load_policy(args.candidate)
        baseline = load_policy(args.baseline) if args.baseline else None
    except Exception as exc:
        raise CliError(f"cannot load policy: {exc}") from exc
    events = load_history(args.history)
    report = backtest(events, candidate, baseline=baseline)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.summary())
    if args.ci:
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as handle:
                handle.write("## Policy backtest (advisory)\n\n```\n")
                handle.write(report.summary())
                handle.write("\n```\n")
    return 0


__all__ = ["add_parser"]
