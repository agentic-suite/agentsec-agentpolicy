"""``agentpolicy calibrate`` — score calibration reports.

Subcommands:
* ``report`` — print false-allow / false-escalate rates bucketed by tool,
  environment, and data class, using the audit log and escalation store.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any

from agentpolicy.audit.logger import AuditLogger
from agentpolicy.calibration import calibrate
from agentpolicy.cli.errors import CliError


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy calibrate`` subcommand parser.

    Args:
        subparsers: The ``add_subparsers()`` action from the parent parser.
    """
    parser = subparsers.add_parser(
        "calibrate",
        help="Score calibration reports: false-allow/escalate rates",
    )
    sub = parser.add_subparsers(dest="calibrate_command", required=True)

    sub.add_parser(
        "report",
        help="Show false-allow and false-escalate rates by tool, env, data class",
    ).add_argument("--json", action="store_true", help="emit the calibration report as JSON")
    parser.set_defaults(func=_run_calibrate)


def _run_calibrate(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate subcommand."""
    if args.calibrate_command == "report":
        return _run_report(args)
    raise CliError(f"Unknown calibrate subcommand: {args.calibrate_command}")


def _run_report(args: argparse.Namespace) -> int:
    """Compute and print the calibration report (buckets + shadow rates)."""
    logger = AuditLogger()
    entries = logger.query(None)
    report = calibrate(entries)

    if getattr(args, "json", False):
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return 0

    by_tool: defaultdict[str, list[str]] = defaultdict(list)
    by_env: defaultdict[str, list[str]] = defaultdict(list)
    by_data: defaultdict[str, list[str]] = defaultdict(list)

    for entry in entries:
        by_tool[entry.tool].append(entry.decision)
        by_env[entry.environment].append(entry.decision)
        by_data[entry.data_class].append(entry.decision)

    print("=== Calibration Report ===\n")
    _print_bucket("Tool", by_tool)
    _print_bucket("Environment", by_env)
    _print_bucket("Data Class", by_data)

    print("\n=== Shadow calibration ===")
    print(f"  shadow decisions: {report.shadow} / {report.total}")
    print(
        f"  would-block: {report.would_block} "
        f"(false-block candidates {report.false_block}, rate {report.false_block_rate:.0%})"
    )
    print(
        f"  allowed: {report.allowed} "
        f"(false-miss candidates {report.false_miss}, rate {report.false_miss_rate:.0%})"
    )
    if report.threshold_table:
        table = ", ".join(f"{k} x{v}" for k, v in sorted(report.threshold_table.items()))
        print(f"  counterfactual thresholds: {table}")
    return 0


def _print_bucket(label: str, buckets: dict[str, list[str]]) -> None:
    print(f"--- By {label} ---")
    for key, decisions in sorted(buckets.items()):
        total = len(decisions)
        deny_count = sum(1 for d in decisions if d == "deny")
        allow_count = sum(1 for d in decisions if d in ("allow", "audit"))
        escalate_count = sum(1 for d in decisions if d == "escalate")
        print(
            f"  {key}: {total} calls, "
            f"{allow_count} allow/audit ({allow_count/total*100:.0f}%), "
            f"{escalate_count} escalate ({escalate_count/total*100:.0f}%), "
            f"{deny_count} deny ({deny_count/total*100:.0f}%)"
        )
