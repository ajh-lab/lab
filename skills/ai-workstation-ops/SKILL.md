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
- Ollama endpoint: `http://127.0.0.1:11434/v1`
- LiteLLM internal Hermes endpoint: `http://127.0.0.1:4004/v1`
- LiteLLM authenticated LAN endpoint for Cline/external clients: `http://192.168.1.123:4000/v1`
- LiteLLM metrics proxy: `http://192.168.1.123:4001/metrics`

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

## LiteLLM And Cline

The workstation uses a split-port LiteLLM setup:

- `litellm-ollama-proxy.service`: internal backend on `127.0.0.1:4004`.
- `litellm-lan-auth-proxy.service`: LAN OpenAI-compatible proxy on `0.0.0.0:4000`.
- `litellm-metrics-proxy.service`: metrics-only proxy on `0.0.0.0:4001`.

Hermes profiles use `http://127.0.0.1:4004/v1`. Cline and other LAN clients use `http://192.168.1.123:4000/v1` with the bearer key stored in OpenBAO at `secret/homelab/providers/litellm`, field `lan_api_key`. Do not print the key.

Health checks:

```bash
systemctl --user is-active litellm-ollama-proxy.service litellm-lan-auth-proxy.service litellm-metrics-proxy.service
ss -ltnp | grep -E ':4000|:4001|:4004'
```

## Model Profiles

Current intended split:

- default profile: local `hermes-qwen3-coder:30b-256k` through LiteLLM/Ollama
- `qwen3-coder-128k-worker`: lean Kanban worker profile for normal coding cards
- `qwen3-coder-128k-fast-chat`: preferred direct browser chat profile for normal Q&A
- `qwen3-coder-256k-fast-chat`: browser chat profile only when large context is needed
- `deepseek-v4-flash`: normal paid DeepSeek work through LiteLLM
- `deepseek-v4-pro`: complex planning, review, difficult debugging, or failed-card recovery

Check profiles:

```bash
hermes profile list
hermes -p deepseek-v4-flash doctor
```

Do not print API keys. Store provider keys in OpenBAO and/or profile `.env` only as a controlled fallback.
