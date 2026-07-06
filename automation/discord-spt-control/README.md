# SPT Discord Control Bot

This folder contains the deterministic Discord control surface for the SPT/Fika
service on `SPT02` (`192.168.1.86`).

The bot is intentionally separate from the general Hermes Discord gateway. It
does not call an LLM and does not pass user text to Hermes. It only accepts the
fixed commands below in the configured Discord channel:

- `status`
- `start`
- `restart`
- `help`

The action commands call the existing SPT02 non-interactive script through SSH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status
```

## ai-workstation deployment

Expected install path:

```text
~/.local/share/lab/spt-discord-control
```

Systemd user service:

```text
~/.config/systemd/user/spt-discord-control.service
```

Runtime config:

```text
~/.config/spt-discord-control/config.env
```

Required environment variables:

```text
SPT_DISCORD_CHANNEL_ID=<private Discord channel ID>
SPT_SSH_HOST=192.168.1.86
SPT_SSH_USER=helios
```

`DISCORD_BOT_TOKEN` is expected to come from the existing Hermes environment at
`~/.hermes/.env`; do not duplicate the token in this service config unless the
Hermes env file is no longer available.

Optional environment variables:

```text
SPT_DISCORD_ALLOWED_USER_IDS=<comma-separated Discord user IDs>
SPT_DISCORD_ALLOWED_ROLE_IDS=<comma-separated Discord role IDs>
SPT_CONTROL_COOLDOWN_SECONDS=120
SPT_CONTROL_COMMAND_TIMEOUT_SECONDS=1200
SPT_CONTROL_STATUS_TIMEOUT_SECONDS=45
```

If the allowlist variables are empty, access is controlled by Discord channel
permissions. The recommended Discord setup is a private channel hidden from
`@everyone`, with only the Helios bot and selected users/roles allowed.

Hermes should be restricted to the normal `#helios` channel with
`DISCORD_ALLOWED_CHANNELS` so the general agent does not answer in the SPT admin
channel.
