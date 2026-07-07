---
name: ai-workstation-ops
description: Operate and maintain the ai-workstation lab host and Hermes runtime. Use for Fedora OS updates, reboots, Hermes upgrades, Ollama/qwen3-coder model checks, Hermes gateway/dashboard services, DeepSeek profile setup, OpenBAO sudo injection, and workstation health checks.
---

# AI Workstation Ops

## Host

- Hostname: `ai-workstation-evox2`
- SSH target: `helios@192.168.1.123`
- OS: Fedora 43
- Persistent AI storage: `/mnt/ai`
- Local model endpoint: `http://127.0.0.1:11434/v1`

Read `automation/ai-workstation/README.md` and `ai-baseline-context.md` before substantial changes.

## Core Checks

```bash
ssh helios@192.168.1.123 'hostnamectl; hermes --version; systemctl --user --no-pager status hermes-gateway.service hermes-dashboard.service'
```

Hermes services:

- `hermes-gateway.service`
- `hermes-dashboard.service`
- dashboard bound to `127.0.0.1:9119`

Dashboard access from Windows:

```powershell
ssh -L 9119:127.0.0.1:9119 helios@192.168.1.123
```

## OpenBAO And Sudo

Use the workstation helper for bootstrap secrets:

```bash
openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null && echo OK
```

Hermes sudo support is injected by `/home/helios/.local/bin/hermes-openbao-sudo-env` through user systemd drop-ins. Do not put sudo passwords in Hermes config or logs.

## Updates

For OS updates, check before applying:

```bash
dnf check-update
flatpak update --appstream
```

If applying updates, use `sudo dnf upgrade --refresh` through the established sudo path, then reboot if required. After reboot, verify SSH, kernel, failed units, and Hermes services.

## Hermes

Before updating Hermes, check local modifications in `/home/helios/.hermes/hermes-agent`; preserve local patches and do not discard user changes. After update:

```bash
hermes --version
systemctl --user restart hermes-gateway.service hermes-dashboard.service
systemctl --user is-active hermes-gateway.service hermes-dashboard.service
```

## Model Profiles

Current intended split:

- default profile: local `hermes-qwen3-coder:30b-64k`
- `deepseek` profile: DeepSeek direct API once `DEEPSEEK_API_KEY` is configured

Check profiles:

```bash
hermes profile list
hermes -p deepseek doctor
```

Do not print API keys. Store provider keys in OpenBAO and/or profile `.env` only as a controlled fallback.
