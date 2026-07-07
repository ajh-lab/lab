---
name: spt-fika-ops
description: Operate, troubleshoot, and document the SPT/Fika Escape From Tarkov server in the lab. Use for SPT02 status/start/restart, Fika headless checks, Discord control bot work, mod/package documentation, player setup, and SPT/Fika Wiki.js runbook updates.
---

# SPT/Fika Ops

## Hosts And Sources

- SPT/Fika server: `SPT02` at `192.168.1.86`
- Control source: `ai-workstation-evox2` (`helios@192.168.1.123`)
- Backend URL: `https://192.168.1.86:6969`
- Headless endpoint: `https://192.168.1.86:6969/fika/headless/get`
- Main runbook: `docs/spt-fika-runbook.md`
- Wiki.js upsert: `automation/wikijs/scripts/upsert-spt-fika-page.ps1`

## Safe Remote Control

Use the non-interactive action script on SPT02. Do not use the interactive menu from Hermes/Discord.

From ai-workstation:

```bash
ssh helios@192.168.1.86 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SPT\automation\Invoke-SPT02-FikaAction.ps1 -Action Status'
```

Valid actions are `Status`, `Start`, `Stop`, and `Restart`. For delegated Discord users, expose only `status`, `start`, and `restart` through the restricted control bot.

Repo sources:

- `automation/spt02/Invoke-SPT02-FikaAction.ps1`
- `automation/spt02/Manage-SPT02-Fika.ps1`
- `automation/spt02/Start-FikaHeadlessAfterServer.ps1`
- `automation/discord-spt-control/`
- `automation/spt-client/Install-SPTFikaPlayerClient.ps1`

## Status Expectations

Healthy status should show:

- `sptServerRunning: true`
- `fikaHeadlessManagerRunning: true`
- `escapeFromTarkovRunning: true`
- `port6969Listening: true`
- `backendReady: true`
- headless endpoint with at least one registered headless client after EFT finishes loading

## Secrets

SPT02 credentials live in OpenBAO at `secret/homelab/vms/spt02`. The Fika Discord Presence webhook and Fika API key are secrets configured only on SPT02. Do not write these values to Git, Wiki.js, Discord, Kanban comments, or logs.

## Discord Control Bot

Restricted SPT admin channel work uses `automation/discord-spt-control/`. The bot is deterministic, not LLM-backed, and accepts only `status`, `start`, `restart`, and `help`.

Installed path on ai-workstation:

```text
/home/helios/.local/share/lab/spt-discord-control
```

Systemd user unit:

```text
spt-discord-control.service
```

## Documentation

After SPT/Fika changes:

- update `docs/spt-fika-runbook.md`
- run or update `automation/wikijs/scripts/upsert-spt-fika-page.ps1`
- update `ai-baseline-context.md` if host, ports, secrets, service state, or control paths changed
