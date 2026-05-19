---
name: lab-ops
description: Home lab operations workflow for the lab repo, OpenBao/OpenBAO secrets, k3s, NetBox, Wiki.js, n8n, observability, and ai-workstation/Hermes tasks. Use when Codex or Helios is asked to operate, debug, deploy, document, or retrieve credentials for this home lab, especially when the user mentions OpenBao, OpenBAO, secrets, sudo, ai-workstation, Hermes, Discord, k3s, NetBox, n8n, Wiki.js, or the lab repo.
---

# Lab Ops

## Locate Context

Find the lab repo before doing operational work. Prefer the current working directory if it is a `lab` checkout. Otherwise check these paths in order:

```text
$LAB_REPO
~/SourceControl/lab
~/sourcecontrol/lab
/mnt/ai/agent/lab
~/lab
```

Once located, read `ai-baseline-context.md` first. For infrastructure-specific work, also read `sub-context/ai-infrastructure-context.md` if it exists. Treat `ai-baseline-context.md`, `network_devices.csv`, and the files under `k8s/` and `automation/` as durable operational context.

## Start Workflow

Before any operational task from the lab repo, run the bootstrap script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File automation\agent\scripts\bootstrap-lab-context.ps1
```

On Linux, use PowerShell if `pwsh` is installed:

```bash
pwsh -NoProfile -ExecutionPolicy Bypass -File automation/agent/scripts/bootstrap-lab-context.ps1
```

If PowerShell is unavailable, continue with read-only context gathering and report that bootstrap could not run.

## Secrets And OpenBao

Use OpenBao/OpenBAO first. The primary endpoint is `http://192.168.1.25:8200`, the KV mount is `secret`, and the bootstrap snapshot path is `secret/homelab/bootstrap/env`.

Never print secret values. Do not copy passwords, tokens, or API keys into Markdown, chat, Jira, Slack, Discord, command logs, or committed files.

For automation in this repo, use `automation/common/SecretResolver.psm1` and `Resolve-LabSecret`; do not add new direct `.env` reads. `.env` is only a gitignored bootstrap fallback.

On `ai-workstation-evox2`, use the existing helper for bootstrap fields:

```bash
openbao-env-get FIELD_NAME
```

For the workstation sudo password, the field is `AI_WORKSTATION_PASSWORD` at `secret/homelab/bootstrap/env`. Validate without printing it:

```bash
openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null && echo OK
```

Hermes terminal sudo support expects `SUDO_PASSWORD` in the process environment, supplied by `/home/helios/.local/bin/hermes-openbao-sudo-env` through the user systemd drop-ins. Do not put the password in `~/.hermes/config.yaml`.

## Lab Operating Rules

Keep `network_devices.csv` as the inventory source of truth and update `LastUpdated` on manual inventory edits. Store only credential key references, never raw credentials.

For k3s changes, verify Rancher webhook health before disruptive work. Keep `k8s/helm/*` and `k8s/manifests/*` aligned with runtime state.

For n8n workflow changes, export updated workflow JSON to `automation/n8n/workflows/exports/` and keep reusable templates in `automation/n8n/workflows/templates/`.

For NetBox and UniFi inventory work, use the repo scripts under `automation/netbox/scripts/` and `automation/unifi/scripts/` instead of ad hoc API calls unless debugging.

For ai-workstation and Strix Halo work, read `automation/ai-workstation/README.md` and prefer `automation/ai-workstation/scripts/sync-strix-halo-backend.ps1` for backend sync.

## Discord And Helios Recovery Path

When a Discord interaction with Helios mentions OpenBao/OpenBAO, secrets, credentials, sudo, the workstation, or the lab, immediately orient to the lab repo and this skill. The common failure mode is trying to infer OpenBao details from memory instead of reading `ai-baseline-context.md`.

The minimum recovery sequence is:

```bash
cd ~/SourceControl/lab 2>/dev/null || cd /mnt/ai/agent/lab 2>/dev/null || cd ~/lab
sed -n '1,180p' ai-baseline-context.md
grep -n "OpenBao\|OpenBAO\|Hermes\|AI Workstation Sudo Credential" ai-baseline-context.md
openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null && echo OK
```
