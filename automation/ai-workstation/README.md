# AI Workstation Automation

This folder tracks automation and runbooks for the Fedora AI workstation (`192.168.1.123`).

## OpenClaw Runtime (Side-by-Side with Hermes)

- Installed: `OpenClaw 2026.5.7`
- Install method: official script (`curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard`)
- Binary path: `/home/helios/.npm-global/bin/openclaw`
- Gateway service: `openclaw-gateway.service` (user systemd)
- Current service state: disabled/inactive as of 2026-05-09 while Hermes Discord connectivity is being tested.
- Bind mode: loopback only (`127.0.0.1:18789`)
- Dashboard URL (local on workstation): `http://127.0.0.1:18789/`
- Browser control sidecar: `127.0.0.1:18791` (token-auth)
- Discord channel status: validated 2026-05-09; bot token resolves as `Helios`, configured `helios` channel is readable, and service restart cleared a stale Discord gateway process.

### Security posture

- Gateway token is persisted at:
  - `/home/helios/.config/openclaw/gateway-token`
- Gateway service token environment is injected via systemd drop-in:
  - `/home/helios/.config/systemd/user/openclaw-gateway.service.d/10-env.conf`
- Hermes and OpenClaw run side-by-side as separate user services.
- Hermes status: `hermes-gateway.service` is enabled and active (`Hermes Agent v0.18.0 / 2026.7.1` as of 2026-07-07), with systemd linger enabled.
- Hermes default model: `hermes-qwen3-coder:30b-256k` through local LiteLLM (`http://127.0.0.1:4000/v1`) and Ollama. Hermes config sets `model.context_length=262144` and `model.ollama_num_ctx=262144`.
- Hermes DeepSeek profiles are model-named: `deepseek-v4-flash` and `deepseek-v4-pro`. Do not recreate the removed legacy `deepseek` profile. The DeepSeek key is stored in OpenBao at `secret/homelab/providers/deepseek`, field `api_key`; runtime fallback `.env` files must not be printed or committed.
- Hermes model alias source: `qwen3-coder:30b-a3b-q8_0`; aliases exist for `hermes-qwen3-coder:30b-64k`, `hermes-qwen3-coder:30b-128k`, and `hermes-qwen3-coder:30b-256k`.
- Hermes browser chat latency note: the 256k default increases KV-cache allocation but fits the Strix Halo ROCm memory budget. Full tool-enabled Hermes chat is still mostly prompt/tool overhead.
- ai-workstation monitoring: `node-exporter.service` exposes host metrics on `0.0.0.0:9100`; `ai-workstation-gpu-exporter.service` exposes ROCm/sysfs GPU metrics on `0.0.0.0:9101`. Prometheus scrapes both and the `LiteLLM / Hermes Usage` Grafana dashboard includes an `AI Workstation Health` section.
- Hermes dashboard: `hermes-dashboard.service` is enabled and bound to `127.0.0.1:9119` for SSH-tunneled browser access.
- Hermes OpenBao access: `hermes-gateway.service` and `hermes-dashboard.service` have OpenBao env injected through `20-openbao.conf` drop-ins using read-only policy `hermes-bootstrap-env-read`.
- Hermes OpenBao helper: `/home/helios/.local/bin/openbao-env-get FIELD_NAME` reads fields from `secret/homelab/bootstrap/env`, for example `openbao-env-get AI_WORKSTATION_PASSWORD`.

### Useful commands

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
openclaw --version
openclaw doctor
openclaw gateway status
systemctl --user status openclaw-gateway.service
journalctl --user -u openclaw-gateway.service -n 200 --no-pager
systemctl --user enable --now openclaw-gateway.service
systemctl --user status hermes-gateway.service
journalctl --user -u hermes-gateway.service -n 200 --no-pager
systemctl --user status hermes-dashboard.service
ssh -L 9119:127.0.0.1:9119 helios@192.168.1.123
openbao-env-get AI_WORKSTATION_PASSWORD
ollama ps
ollama show hermes-qwen3-coder:30b-256k
hermes config show
hermes profile list
hermes -p deepseek-v4-flash doctor
systemctl --user status node-exporter.service ai-workstation-gpu-exporter.service
```

## Strix Halo Backend Source

Backend source of truth for ROCm/Vulkan llama.cpp toolboxes:

- GitHub: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote clone path on workstation: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox container: `llama-rocm-7.2.2`
- Toolbox image: `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.2.2`

## Script

- `scripts/sync-strix-halo-backend.ps1`
  - Pulls latest upstream repo on workstation
  - Ensures `llama-rocm-7.2.2` toolbox exists
  - Validates device visibility with `llama-cli --list-devices`

## Required `.env` Keys

- `AI_WORKSTATION_IP`
- `AI_WORKSTATION_USER`
- `AI_WORKSTATION_PASSWORD`
