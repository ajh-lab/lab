#!/usr/bin/env python3
"""Query Hermes Kanban from the Windows lab workspace via SSH.

This script is intentionally read-only. It wraps the Hermes CLI on the
ai-workstation so AI agents do not need to discover the dashboard or touch the
Kanban SQLite database directly.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from typing import Iterable


DEFAULT_SSH_TARGET = "helios@192.168.1.123"
DEFAULT_BOARD = "kalshi-research-bot"


def remote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def run_remote(ssh_target: str, parts: list[str]) -> int:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        ssh_target,
        remote_command(parts),
    ]
    completed = subprocess.run(cmd, text=True)
    return completed.returncode


def board_args(board: str, hermes_args: list[str]) -> list[str]:
    return ["hermes", "kanban", "--board", board, *hermes_args]


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--ssh-target",
        default=DEFAULT_SSH_TARGET,
        help=f"SSH target for ai-workstation. Default: {DEFAULT_SSH_TARGET}",
    )
    common.add_argument(
        "--board",
        default=DEFAULT_BOARD,
        help=f"Hermes board slug. Default: {DEFAULT_BOARD}",
    )

    parser = argparse.ArgumentParser(
        description="Read Hermes Kanban board state from ai-workstation.",
        parents=[common],
    )

    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("boards", parents=[common], help="List Hermes Kanban boards.")

    list_parser = subcommands.add_parser(
        "list",
        parents=[common],
        help="List cards on a board.",
    )
    list_parser.add_argument(
        "--status",
        choices=[
            "archived",
            "blocked",
            "done",
            "ready",
            "review",
            "running",
            "scheduled",
            "todo",
            "triage",
        ],
        help="Optional status filter.",
    )
    list_parser.add_argument("--assignee", help="Optional assignee filter.")
    list_parser.add_argument(
        "--sort",
        default="priority",
        choices=[
            "assignee",
            "created",
            "created-desc",
            "priority",
            "priority-desc",
            "status",
            "title",
            "updated",
        ],
        help="Sort order. Default: priority.",
    )
    list_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    list_parser.add_argument(
        "--archived",
        action="store_true",
        help="Include archived cards.",
    )

    show_parser = subcommands.add_parser("show", parents=[common], help="Show a card.")
    show_parser.add_argument("task_id")

    runs_parser = subcommands.add_parser(
        "runs",
        parents=[common],
        help="Show card run history.",
    )
    runs_parser.add_argument("task_id")
    runs_parser.add_argument("--json", action="store_true", help="Emit JSON.")

    log_parser = subcommands.add_parser(
        "log",
        parents=[common],
        help="Show recent card run log.",
    )
    log_parser.add_argument("task_id")
    log_parser.add_argument(
        "--tail",
        default="20000",
        help="Number of bytes to print from the end of the log. Default: 20000.",
    )

    tail_parser = subcommands.add_parser(
        "tail",
        parents=[common],
        help="Follow card events.",
    )
    tail_parser.add_argument("task_id")
    tail_parser.add_argument(
        "--interval",
        default="2",
        help="Polling interval in seconds. Default: 2.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "boards":
        return run_remote(args.ssh_target, ["hermes", "kanban", "boards", "list"])

    if args.command == "list":
        hermes_args = ["list", "--sort", args.sort]
        if args.status:
            hermes_args.extend(["--status", args.status])
        if args.assignee:
            hermes_args.extend(["--assignee", args.assignee])
        if args.json:
            hermes_args.append("--json")
        if args.archived:
            hermes_args.append("--archived")
        return run_remote(args.ssh_target, board_args(args.board, hermes_args))

    if args.command == "show":
        return run_remote(args.ssh_target, board_args(args.board, ["show", args.task_id]))

    if args.command == "runs":
        hermes_args = ["runs", args.task_id]
        if args.json:
            hermes_args.append("--json")
        return run_remote(args.ssh_target, board_args(args.board, hermes_args))

    if args.command == "log":
        return run_remote(
            args.ssh_target,
            board_args(args.board, ["log", args.task_id, "--tail", args.tail]),
        )

    if args.command == "tail":
        return run_remote(
            args.ssh_target,
            board_args(args.board, ["tail", args.task_id, "--interval", args.interval]),
        )

    return 2


if __name__ == "__main__":
    sys.exit(main())
