"""``agentpolicy freeze`` — declare/expire/list change freezes (WBS M15 ``15.1``).

A declared freeze tightens the posture for its window and every decision carries
the ``freeze_id``. Declare/expire are audited events. Store defaults to
``~/.agentpolicy/freezes.json`` (override with ``--store`` or
``AGENTPOLICY_FREEZES_FILE``).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.freeze import FreezeLedger

_DEFAULT_STORE = "~/.agentpolicy/freezes.json"


def _store_path(args: argparse.Namespace) -> str:
    return (
        getattr(args, "store", None)
        or os.environ.get("AGENTPOLICY_FREEZES_FILE")
        or _DEFAULT_STORE
    )


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy freeze`` subcommand parser."""
    parser = subparsers.add_parser(
        "freeze", help="declare / expire / list change freezes",
        description="Manage declared change-freeze windows (tightens the posture).",
    )
    sub = parser.add_subparsers(dest="freeze_command", required=True, metavar="SUBCOMMAND")

    declare = sub.add_parser("declare", help="declare a freeze window")
    declare.add_argument("--env", action="append", required=True, help="environment (repeatable)")
    declare.add_argument("--until", required=True, help="ISO-8601 end of the window")
    declare.add_argument(
        "--from", dest="starts_at", default=None, help="ISO-8601 start (default: now)"
    )
    declare.add_argument("--reason", default="", help="why the freeze is declared")
    declare.add_argument("--store", default=None)
    declare.set_defaults(func=_declare)

    expire = sub.add_parser("expire", help="end a freeze early")
    expire.add_argument("freeze_id")
    expire.add_argument("--store", default=None)
    expire.set_defaults(func=_expire)

    listing = sub.add_parser("list", help="list declared freezes")
    listing.add_argument("--store", default=None)
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(func=_list)


def _declare(args: argparse.Namespace) -> int:
    ledger = FreezeLedger.load(_store_path(args))
    try:
        window = ledger.declare(
            environments=args.env, starts_at=args.starts_at, ends_at=args.until,
            reason=args.reason,
        )
    except ValueError as exc:
        raise CliError(str(exc)) from exc
    ledger.save(_store_path(args))
    print(json.dumps(window.to_dict(), indent=2))
    return 0


def _expire(args: argparse.Namespace) -> int:
    ledger = FreezeLedger.load(_store_path(args))
    window = ledger.expire(args.freeze_id)
    if window is None:
        raise CliError(f"unknown freeze_id {args.freeze_id!r}")
    ledger.save(_store_path(args))
    print(json.dumps(window.to_dict(), indent=2))
    return 0


def _list(args: argparse.Namespace) -> int:
    ledger = FreezeLedger.load(_store_path(args))
    windows = [w.to_dict() for w in ledger.windows.values()]
    if args.json:
        print(json.dumps(windows, indent=2))
        return 0
    if not windows:
        print("No declared freezes.")
        return 0
    for window in windows:
        print(
            f"  {window['freeze_id']}  {','.join(window['environments'])}  "
            f"{window['starts_at']}..{window['ends_at']}  {window['reason']}"
        )
    return 0
