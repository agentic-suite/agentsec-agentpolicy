"""``agentpolicy breakglass`` — elevate/revert/list break-glass windows (WBS M18).

A declared elevation is time-boxed, requires a logged reason, and reverts
automatically at expiry. Store defaults to ``~/.agentpolicy/breakglass.json``
(override with ``--store`` or ``AGENTPOLICY_BREAKGLASS_FILE``).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from agentpolicy.breakglass import BreakGlassLedger
from agentpolicy.cli.errors import CliError

_DEFAULT_STORE = "~/.agentpolicy/breakglass.json"


def _store_path(args: argparse.Namespace) -> str:
    return (
        getattr(args, "store", None)
        or os.environ.get("AGENTPOLICY_BREAKGLASS_FILE")
        or _DEFAULT_STORE
    )


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy breakglass`` subcommand parser."""
    parser = subparsers.add_parser(
        "breakglass", help="elevate / revert / list break-glass windows",
        description="Manage time-boxed break-glass elevations (widens scope ceilings only).",
    )
    sub = parser.add_subparsers(dest="breakglass_command", required=True, metavar="SUBCOMMAND")

    elevate = sub.add_parser("elevate", help="declare a time-boxed elevation")
    elevate.add_argument("--agent", required=True, help="the elevated agent identity")
    elevate.add_argument("--env", action="append", required=True, help="environment (repeatable)")
    elevate.add_argument("--until", default=None, help="ISO-8601 end (default: now + --ttl)")
    elevate.add_argument("--ttl", type=int, default=None, help="TTL seconds (default 900)")
    elevate.add_argument(
        "--from", dest="starts_at", default=None, help="ISO-8601 start (default: now)"
    )
    elevate.add_argument("--reason", required=True, help="why the elevation is needed (mandatory)")
    elevate.add_argument("--store", default=None)
    elevate.set_defaults(func=_elevate)

    revert = sub.add_parser("revert", help="end an elevation early")
    revert.add_argument("break_glass_id")
    revert.add_argument("--store", default=None)
    revert.set_defaults(func=_revert)

    listing = sub.add_parser("list", help="list declared elevations")
    listing.add_argument("--store", default=None)
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=_list)


def _elevate(args: argparse.Namespace) -> int:
    ledger = BreakGlassLedger.load(_store_path(args))
    try:
        window = ledger.elevate(
            agent_id=args.agent, environments=args.env, ends_at=args.until,
            ttl_seconds=args.ttl, starts_at=args.starts_at, reason=args.reason,
        )
    except ValueError as exc:
        raise CliError(str(exc)) from exc
    ledger.save(_store_path(args))
    print(json.dumps(window.to_dict(), indent=2))
    return 0


def _revert(args: argparse.Namespace) -> int:
    ledger = BreakGlassLedger.load(_store_path(args))
    window = ledger.revert(args.break_glass_id)
    if window is None:
        raise CliError(f"unknown break_glass_id {args.break_glass_id!r}")
    ledger.save(_store_path(args))
    print(json.dumps(window.to_dict(), indent=2))
    return 0


def _list(args: argparse.Namespace) -> int:
    ledger = BreakGlassLedger.load(_store_path(args))
    ledger.sweep()
    windows = [w.to_dict() for w in ledger.windows.values()]
    if args.json:
        print(json.dumps(windows, indent=2))
        return 0
    if not windows:
        print("No declared elevations.")
        return 0
    for window in windows:
        print(
            f"  {window['break_glass_id']}  {window['agent_id']}  "
            f"{','.join(window['environments'])}  {window['starts_at']}..{window['ends_at']}  "
            f"{window['reason']}"
        )
    return 0


__all__ = ["add_parser"]
