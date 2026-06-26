#!/usr/bin/env python3
"""Perform safe Hermes Kanban recovery actions via SSH.

This replaces older direct SQLite edits. Prefer official Hermes operations:

- comment: add diagnostic context.
- unblock: move a blocked card back into the active queue.
- reclaim: release a stale running claim.
- promote: start or requeue a ready/todo card when dependencies are satisfied.

The script prints the card before and after the action to make state changes
easy for AI agents to verify.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from typing import Iterable


DEFAULT_SSH_TARGET = "helios@192.168.1.123"
DEFAULT_BOARD = "kalshi-research-bot"
DEFAULT_AUTHOR = "cline"


def remote_command(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def run_remote(ssh_target: str, parts: list[str], check: bool = False) -> int:
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
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, cmd)
    return completed.returncode


def board_args(board: str, hermes_args: list[str]) -> list[str]:
    return ["hermes", "kanban", "--board", board, *hermes_args]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely recover or annotate Hermes Kanban cards.",
    )
    parser.add_argument("task_id", help="Hermes task/card id, for example t_b4c17c0e.")
    parser.add_argument(
        "--ssh-target",
        default=DEFAULT_SSH_TARGET,
        help=f"SSH target for ai-workstation. Default: {DEFAULT_SSH_TARGET}",
    )
    parser.add_argument(
        "--board",
        default=DEFAULT_BOARD,
        help=f"Hermes board slug. Default: {DEFAULT_BOARD}",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["comment", "unblock", "reclaim", "promote"],
        help="Official Hermes action to perform.",
    )
    parser.add_argument(
        "--reason",
        required=True,
        help="Human-readable reason/comment. Do not include secrets.",
    )
    parser.add_argument(
        "--author",
        default=DEFAULT_AUTHOR,
        help=f"Comment author for action=comment. Default: {DEFAULT_AUTHOR}",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Only applies to promote; bypasses dependency checks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only applies to promote; validates without mutating state.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required to mutate card state. Without this, only shows the card.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    print("=== Before ===", flush=True)
    before_rc = run_remote(args.ssh_target, board_args(args.board, ["show", args.task_id]))
    if before_rc != 0:
        return before_rc

    if not args.yes and not args.dry_run:
        print(
            "\nNo mutation performed. Re-run with --yes after reviewing the card.",
            flush=True,
        )
        return 0

    if args.action == "comment":
        action_args = [
            "comment",
            "--author",
            args.author,
            args.task_id,
            args.reason,
        ]
    elif args.action == "unblock":
        action_args = ["unblock", args.task_id, "--reason", args.reason]
    elif args.action == "reclaim":
        action_args = ["reclaim", args.task_id, "--reason", args.reason]
    elif args.action == "promote":
        action_args = ["promote"]
        if args.force:
            action_args.append("--force")
        if args.dry_run:
            action_args.append("--dry-run")
        action_args.extend([args.task_id, args.reason])
    else:
        return 2

    print("\n=== Action ===", flush=True)
    action_rc = run_remote(args.ssh_target, board_args(args.board, action_args))
    if action_rc != 0:
        return action_rc

    if not args.dry_run:
        print("\n=== After ===", flush=True)
        return run_remote(args.ssh_target, board_args(args.board, ["show", args.task_id]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
