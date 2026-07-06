#!/usr/bin/env python3
"""Restricted Discord control bot for the SPT/Fika service on SPT02."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
from dataclasses import dataclass
from typing import Any

import discord


ACTION_BY_COMMAND = {
    "status": "Status",
    "spt status": "Status",
    "!status": "Status",
    "!spt status": "Status",
    "start": "Start",
    "spt start": "Start",
    "!start": "Start",
    "!spt start": "Start",
    "restart": "Restart",
    "spt restart": "Restart",
    "!restart": "Restart",
    "!spt restart": "Restart",
}


@dataclass(frozen=True)
class Settings:
    token: str
    channel_id: int
    ssh_host: str = "192.168.1.86"
    ssh_user: str = "helios"
    action_script: str = r"C:\SPT\automation\Invoke-SPT02-FikaAction.ps1"
    allowed_user_ids: frozenset[int] = frozenset()
    allowed_role_ids: frozenset[int] = frozenset()
    cooldown_seconds: int = 120
    command_timeout_seconds: int = 1200
    status_timeout_seconds: int = 45


def _parse_id_set(raw: str | None) -> frozenset[int]:
    values: set[int] = set()
    for part in (raw or "").split(","):
        cleaned = part.strip()
        if cleaned:
            values.add(int(cleaned))
    return frozenset(values)


def load_settings() -> Settings:
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    channel_id_raw = os.environ.get("SPT_DISCORD_CHANNEL_ID", "").strip()
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    if not channel_id_raw:
        raise RuntimeError("SPT_DISCORD_CHANNEL_ID is required")

    return Settings(
        token=token,
        channel_id=int(channel_id_raw),
        ssh_host=os.environ.get("SPT_SSH_HOST", "192.168.1.86").strip(),
        ssh_user=os.environ.get("SPT_SSH_USER", "helios").strip(),
        action_script=os.environ.get(
            "SPT_ACTION_SCRIPT", r"C:\SPT\automation\Invoke-SPT02-FikaAction.ps1"
        ).strip(),
        allowed_user_ids=_parse_id_set(os.environ.get("SPT_DISCORD_ALLOWED_USER_IDS")),
        allowed_role_ids=_parse_id_set(os.environ.get("SPT_DISCORD_ALLOWED_ROLE_IDS")),
        cooldown_seconds=int(os.environ.get("SPT_CONTROL_COOLDOWN_SECONDS", "120")),
        command_timeout_seconds=int(
            os.environ.get("SPT_CONTROL_COMMAND_TIMEOUT_SECONDS", "1200")
        ),
        status_timeout_seconds=int(os.environ.get("SPT_CONTROL_STATUS_TIMEOUT_SECONDS", "45")),
    )


def normalize_command(content: str, bot_user_id: int | None) -> str:
    text = content.strip().lower()
    if bot_user_id is not None:
        mention_patterns = [
            rf"^<@!?{bot_user_id}>\s*",
            rf"\s*<@!?{bot_user_id}>$",
        ]
        for pattern in mention_patterns:
            text = re.sub(pattern, "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


class SptControlBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = bool(settings.allowed_role_ids)
        super().__init__(intents=intents)
        self.settings = settings
        self._last_mutating_action_at = 0.0

    async def on_ready(self) -> None:
        print(f"SPT Discord control bot ready as {self.user}", flush=True)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != self.settings.channel_id:
            return

        command = normalize_command(message.content, self.user.id if self.user else None)
        if command in {"help", "!help", "spt help", "!spt help"}:
            await message.channel.send(
                "SPT/Fika commands: `status`, `start`, `restart`. "
                "This channel does not provide general Helios chat access."
            )
            return

        action = ACTION_BY_COMMAND.get(command)
        if not action:
            await message.channel.send(
                "I can only run `status`, `start`, or `restart` for SPT/Fika."
            )
            return

        if not self._is_authorized(message.author):
            await message.channel.send("You are not authorized to control SPT/Fika here.")
            return

        if action in {"Start", "Restart"} and not self._cooldown_ready():
            await message.channel.send("A start/restart was requested recently. Try again shortly.")
            return

        if action in {"Start", "Restart"}:
            self._last_mutating_action_at = asyncio.get_running_loop().time()
            await message.channel.send(f"Running `{action.lower()}` on SPT02...")

        async with message.channel.typing():
            result = await self._run_spt_action(action)
        await message.channel.send(format_status_message(action, result))

    def _is_authorized(self, author: discord.abc.User) -> bool:
        if self.settings.allowed_user_ids and author.id not in self.settings.allowed_user_ids:
            return False
        if self.settings.allowed_role_ids:
            member_roles = {role.id for role in getattr(author, "roles", [])}
            if not (member_roles & self.settings.allowed_role_ids):
                return False
        return True

    def _cooldown_ready(self) -> bool:
        if self._last_mutating_action_at <= 0:
            return True
        elapsed = asyncio.get_running_loop().time() - self._last_mutating_action_at
        return elapsed >= self.settings.cooldown_seconds

    async def _run_spt_action(self, action: str) -> dict[str, Any]:
        timeout = (
            self.settings.status_timeout_seconds
            if action == "Status"
            else self.settings.command_timeout_seconds
        )
        ssh_target = f"{self.settings.ssh_user}@{self.settings.ssh_host}"
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=10",
            ssh_target,
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            self.settings.action_script,
            "-Action",
            action,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode(errors="replace").strip()
        err = stderr.decode(errors="replace").strip()
        if proc.returncode != 0:
            raise RuntimeError(
                f"SPT action failed with exit code {proc.returncode}: {err or out}"
            )
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            quoted = shlex.quote(out[:500])
            raise RuntimeError(f"SPT action returned non-JSON output: {quoted}") from exc


def _headless_summary(raw: Any) -> str:
    if not raw:
        return "no endpoint data"
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        return "endpoint returned non-JSON data"
    headlesses = data.get("headlesses") or {}
    if not headlesses:
        return "none registered"
    return f"{len(headlesses)} registered"


def _bool_word(value: Any) -> str:
    return "yes" if bool(value) else "no"


def format_status_message(action: str, status: dict[str, Any]) -> str:
    title = "SPT/Fika Status" if action == "Status" else f"SPT/Fika {action} Complete"
    lines = [
        f"**{title}**",
        f"Host: `{status.get('computerName', 'SPT02')}` (`192.168.1.86`)",
        f"Backend ready: **{_bool_word(status.get('backendReady'))}**",
        f"Port 6969 listening: **{_bool_word(status.get('port6969Listening'))}**",
        f"SPT server running: **{_bool_word(status.get('sptServerRunning'))}**",
        f"Fika headless manager running: **{_bool_word(status.get('fikaHeadlessManagerRunning'))}**",
        f"EFT headless process running: **{_bool_word(status.get('escapeFromTarkovRunning'))}**",
        f"Headless endpoint: **{_headless_summary(status.get('headlessEndpoint'))}**",
        f"Timestamp: `{status.get('timestamp', 'unknown')}`",
    ]
    return "\n".join(lines)


async def main() -> None:
    settings = load_settings()
    bot = SptControlBot(settings)
    async with bot:
        await bot.start(settings.token)


if __name__ == "__main__":
    asyncio.run(main())
