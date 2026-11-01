"""``agentpolicy approve`` / ``deny`` / ``ask list`` — resolve the human gate (M7 ``7.2``).

A Cedar ``ask`` decision is a pending :class:`~agentpolicy.ask.Ask`. A human
resolves it with ``agentpolicy approve <ask_id>`` or ``agentpolicy deny
<ask_id>``; the agent resumes by re-submitting the call with the ``ask_id``.
The store defaults to ``~/.agentpolicy/asks.json`` (override with ``--store`` or
``AGENTPOLICY_ASKS_FILE``).
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
from typing import Any

from agentpolicy.ask import AskBroker
from agentpolicy.cli.errors import CliError

_DEFAULT_STORE = "~/.agentpolicy/asks.json"


def _store_path(args: argparse.Namespace) -> str:
    return (
        getattr(args, "store", None)
        or os.environ.get("AGENTPOLICY_ASKS_FILE")
        or _DEFAULT_STORE
    )


def _approver(args: argparse.Namespace) -> str:
    who = getattr(args, "approver", None)
    if who:
        return str(who)
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def add_parser(subparsers: Any) -> None:
    """Register the ``approve``, ``deny``, and ``ask`` subcommand parsers."""
    approve = subparsers.add_parser(
        "approve", help="approve a pending ask",
        description="Approve a pending ask so the agent's call may execute.",
    )
    approve.add_argument("ask_id", help="the ask id to approve")
    approve.add_argument("--approver", help="approver identity (default: current user)")
    approve.add_argument("--store", help="path to the asks store")
    approve.set_defaults(func=_approve)

    deny = subparsers.add_parser(
        "deny", help="deny a pending ask",
        description="Deny a pending ask; the agent resumes with the reason.",
    )
    deny.add_argument("ask_id", help="the ask id to deny")
    deny.add_argument("--approver", help="approver identity (default: current user)")
    deny.add_argument("--reason", default="", help="human-readable denial reason")
    deny.add_argument("--store", help="path to the asks store")
    deny.set_defaults(func=_deny)

    ask = subparsers.add_parser(
        "ask", help="inspect pending asks",
        description="List the pending human gates.",
    )
    ask_sub = ask.add_subparsers(dest="ask_command", required=True, metavar="SUBCOMMAND")
    listing = ask_sub.add_parser("list", help="list pending asks")
    listing.add_argument("--store", help="path to the asks store")
    listing.add_argument("--json", action="store_true", help="emit JSON")
    listing.set_defaults(func=_list)


def _approve(args: argparse.Namespace) -> int:
    broker = AskBroker.load(_store_path(args))
    try:
        record = broker.approve(args.ask_id, approver=_approver(args))
    except ValueError as exc:
        raise CliError(str(exc)) from exc
    broker.save(_store_path(args))
    print(json.dumps(record.to_dict(), indent=2))
    return 0


def _deny(args: argparse.Namespace) -> int:
    broker = AskBroker.load(_store_path(args))
    try:
        record = broker.deny(args.ask_id, approver=_approver(args), reason=args.reason)
    except ValueError as exc:
        raise CliError(str(exc)) from exc
    broker.save(_store_path(args))
    print(json.dumps(record.to_dict(), indent=2))
    return 0


def _list(args: argparse.Namespace) -> int:
    broker = AskBroker.load(_store_path(args))
    pending = [r.to_dict() for r in broker.pending()]
    if args.json:
        print(json.dumps(pending, indent=2))
        return 0
    if not pending:
        print("No pending asks.")
        return 0
    for record in pending:
        print(
            f"  {record['ask_id']}  {record['action']} {record['tool']} "
            f"in {record['environment']} ({record['data_class']}) — {record['reason']}"
        )
    return 0
