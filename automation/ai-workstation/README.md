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
- Hermes default model: `hermes-qwen3-coder:30b-256k` through local LiteLLM (`http://127.0.0.1:4004/v1`) and Ollama. Hermes config sets `model.context_length=262144` and `model.ollama_num_ctx=262144`.
- Hermes DeepSeek profiles are model-named: `deepseek-v4-flash` and `deepseek-v4-pro`. Do not recreate the removed legacy `deepseek` profile. The DeepSeek key is stored in OpenBao at `secret/homelab/providers/deepseek`, field `api_key`; runtime fallback `.env` files must not be printed or committed.
- Hermes model alias source: `qwen3-coder:30b-a3b-q8_0`; aliases exist for `hermes-qwen3-coder:30b-64k`, `hermes-qwen3-coder:30b-128k`, and `hermes-qwen3-coder:30b-256k`.
- Hermes browser chat latency note: the 256k default increases KV-cache allocation but fits the Strix Halo ROCm memory budget. Full tool-enabled Hermes chat is still mostly prompt/tool overhead and can loop on lightweight questions. For direct browser chat, prefer `qwen3-coder-128k-fast-chat` or `qwen3-coder-256k-fast-chat`; those profiles restrict CLI tools to web only, disable local action tools, set `agent.max_turns: 4`, and disable environment probing.
- Hermes Kanban worker profile: `qwen3-coder-128k-worker` is the preferred local worker for normal coding cards. It uses `hermes-qwen3-coder:30b-128k`, keeps only terminal/file/code-execution/todo/skills tools, disables browser/image/TTS/computer-use/delegation/cron/memory extras, sets `agent.max_turns: 28`, sets `agent.reasoning_effort: none` so Ollama does not receive unsupported thinking requests, and disables environment probing with a fixed lab workspace hint. Use larger/full profiles only when the card needs broader tools or 256k context.
- Qwen3.8 BF16 tool-enabled test profile: `qwen38bf16tools` uses LiteLLM model `qwen3.8-27b-bf16`, alias `/home/helios/.local/bin/qwen38-bf16-tools`, and the user service `llama-qwen38-bf16.service` on `http://127.0.0.1:11437/v1`. The model file came from Ollama tag `qwen3.8:27b-bf16` and is stored under `/mnt/ai/ollama-qwen38/models`; Ollama `0.32.14` can download/show the model but was not the working runtime because it under-offloaded this dense BF16 model on Strix Halo and hit system-memory OOM. Use the refreshed `llama-rocm-7.14` toolbox for this model. The profile keeps Hermes' full default tool surface enabled; web search still requires a configured Hermes search/tool-gateway API key. Existing Custom endpoint model picker lists include the qwen3-coder aliases, both DeepSeek models, and `qwen3.8-27b-bf16`.
- LiteLLM split-port routing: `litellm-ollama-proxy.service` is the internal backend on `127.0.0.1:4004`; Hermes profiles use this loopback endpoint. `litellm-lan-auth-proxy.service` exposes the OpenAI-compatible API on `0.0.0.0:4000` for LAN clients such as Cline and requires a bearer key. The key is stored in OpenBao at `secret/homelab/providers/litellm`, field `lan_api_key`, with local runtime copy `/home/helios/.config/litellm/litellm-lan-api-key.env`. Cline should use base URL `http://192.168.1.123:4000/v1` and that key.
- LiteLLM package status: `/home/helios/.local/share/litellm/venv` was upgraded from LiteLLM `1.91.0` to `1.97.0` on 2026-08-18 after restoring `pip` in the venv. Freeze backups are under `/home/helios/.local/share/litellm/backups/`.
- ai-workstation monitoring: `node-exporter.service` exposes host metrics on `0.0.0.0:9100`; `ai-workstation-gpu-exporter.service` exposes ROCm/sysfs GPU metrics on `0.0.0.0:9101`. Prometheus scrapes both and the `LiteLLM / Hermes Usage` Grafana dashboard includes an `AI Workstation Health` section.
- Hermes dashboard: `hermes-dashboard.service` is enabled and bound to `127.0.0.1:9119` for SSH-tunneled browser access.
- Hermes dashboard browser sessions use a stable local session token from `/home/helios/.config/hermes-dashboard/session-token.env`, injected into `hermes-dashboard.service` by `/home/helios/.config/systemd/user/hermes-dashboard.service.d/50-stable-session-token.conf`. This prevents dashboard restarts from invalidating the browser chat websocket token. Do not print or commit the token value.
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
systemctl --user cat hermes-dashboard.service
ssh -L 9119:127.0.0.1:9119 helios@192.168.1.123
openbao-env-get AI_WORKSTATION_PASSWORD
ollama ps
ollama show hermes-qwen3-coder:30b-256k
hermes config show
hermes profile list
qwen3-coder-128k-worker tools list
qwen38-bf16-tools tools list
systemctl --user status llama-qwen38-bf16.service
curl -sS http://127.0.0.1:11437/health
curl -sS http://127.0.0.1:4004/v1/models
curl -sS http://127.0.0.1:4001/metrics | head
hermes -p deepseek-v4-flash doctor
systemctl --user status node-exporter.service ai-workstation-gpu-exporter.service
python3 ~/lab/automation/ai-workstation/scripts/benchmark-hermes-models.py --provider litellm --show-ollama-ps
```

## Local Model Benchmarking

Use `scripts/benchmark-hermes-models.py` on the ai-workstation when changing Ollama aliases, Hermes profiles, context windows, or LiteLLM routing. The script runs dependency-free with Python 3 and can target either the LiteLLM OpenAI-compatible endpoint or Ollama's native API.

Recommended first pass:

```bash
cd ~/lab
python3 automation/ai-workstation/scripts/benchmark-hermes-models.py \
  --provider litellm \
  --models hermes-qwen3-coder:30b-64k,hermes-qwen3-coder:30b-128k,hermes-qwen3-coder:30b-256k \
  --jsonl /tmp/hermes-model-benchmark.jsonl \
  --show-ollama-ps
```

Use the Ollama provider when you need native prompt/eval token-per-second counters:

```bash
python3 automation/ai-workstation/scripts/benchmark-hermes-models.py \
  --provider ollama \
  --models hermes-qwen3-coder:30b-128k,hermes-qwen3-coder:30b-256k \
  --scenarios smoke,rust-light \
  --jsonl /tmp/hermes-ollama-benchmark.jsonl \
  --show-ollama-ps
```

For practical Hermes use, prefer the smallest context profile that fits the task. The 256k alias fits the workstation memory budget, but it allocates a much larger KV cache than 64k or 128k and should be treated as a large-context profile, not automatically assumed to be the fastest default.

Observed benchmark results from 2026-07-09:

- Raw Ollama and direct LiteLLM calls are healthy for the qwen3-coder aliases. The `rust-light` scenario generated about 87 output tokens in roughly 2 seconds after model load, around 43-48 output tokens/sec.
- A synthetic long-context prompt of about 10.3k prompt tokens completed in roughly 13 seconds for both 128k and 256k aliases, around 800 prompt tokens/sec.
- The slow 20+ minute browser response was not a raw model throughput problem. It came from full Hermes agent chat using broad tool access, high turn budget, and environment probing. The same Rust-capability prompt completed in about 4-16 seconds with the fast-chat profiles.

Recommended profile usage:

- `qwen3-coder-128k-fast-chat`: default choice for lightweight browser chat and quick Q&A.
- `qwen3-coder-256k-fast-chat`: use when browser chat needs very large context.
- `qwen3-coder-128k`, `qwen3-coder-256k`, or default: use for full development/agent work where terminal, file, and code execution tools are expected.
- `qwen38bf16tools`: use for Qwen3.8 27B BF16 experiments that need the full Hermes tool surface. It is heavier and slower than the qwen3-coder Q8 aliases, but keeps BF16 model weights.

## Strix Halo Backend Source

Backend source of truth for ROCm/Vulkan llama.cpp toolboxes:

- GitHub: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote clone path on workstation: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox containers include `llama-rocm-7.2.2` and refreshed `llama-rocm-7.14`.
- Qwen3.8 BF16 runtime image: `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.14`

## Script

- `scripts/sync-strix-halo-backend.ps1`
  - Pulls latest upstream repo on workstation
  - Ensures `llama-rocm-7.14` toolbox exists
  - Validates device visibility with `llama-cli --list-devices`

## Required `.env` Keys

- `AI_WORKSTATION_IP`
- `AI_WORKSTATION_USER`
- `AI_WORKSTATION_PASSWORD`
