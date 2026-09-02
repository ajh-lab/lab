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
- Hermes status: `hermes-gateway.service` is enabled and active (`Hermes Agent v0.21.0 / 2026.8.31`, upstream `5b0f68b4`, validated 2026-09-01), with systemd linger enabled.
- Hermes default model: `qwen3.8-27b-uncensored-q6_k` through local LiteLLM (`http://127.0.0.1:4004/v1`) and llama.cpp service `llama-qwen38-uncensored-q6k.service` on port `11446`. Hermes config sets `model.context_length=131072` and `model.ollama_num_ctx=131072`. Q4_K_M remains installed as the disabled rollback.
- Hermes DeepSeek profiles are model-named: `deepseek-v4-flash` and `deepseek-v4-pro`. Do not recreate the removed legacy `deepseek` profile. The DeepSeek key is stored in OpenBao at `secret/homelab/providers/deepseek`, field `api_key`; runtime fallback `.env` files must not be printed or committed.
- Hermes model alias source: `qwen3-coder:30b-a3b-q8_0`; aliases exist for `hermes-qwen3-coder:30b-64k`, `hermes-qwen3-coder:30b-128k`, and `hermes-qwen3-coder:30b-256k`. As of 2026-09-02, these LiteLLM routes use `keep_alive: 0`; a direct request to `hermes-qwen3-coder:30b-128k` returned successfully and `ollama ps` was empty 10 seconds later.
- Hermes profile naming: model-specific profiles use `<model>-<variant>-<role>-<context>`, with the context window last. Do not recreate `-fast-chat` names. Use `qwen38-27b-uncensored-q6_k-web-terminal-128k` for Q6 browser chat with terminal access or `qwen3-coder-30b-a3b-q8_0-web-128k` for faster web-only chat.
- Hermes update recovery: the 2026-09-01 update from `v0.20.5` to `v0.21.0` created the full restore archive `/home/helios/.hermes/backups/pre-update-2026-09-01-223739.zip`. The prior local Kanban heartbeat/dashboard patch remains intentionally parked as git stash `hermes-update-autostash-20260902-033801` and as `/home/helios/.hermes/backups/hermes-update-20260902T033737Z/local-source-changes.patch`; do not reapply it blindly because upstream now contains a substantially expanded heartbeat and stale-worker implementation.
- Hermes Kanban worker profile: `qwen3-coder-30b-a3b-q8_0-worker-128k` is the preferred qwen3-coder worker for normal coding cards. It uses `hermes-qwen3-coder:30b-128k`, keeps only terminal/file/code-execution/todo/skills tools, disables browser/image/TTS/computer-use/delegation/cron/memory extras, sets `agent.max_turns: 28`, sets `agent.reasoning_effort: none`, and disables environment probing with a fixed lab workspace hint. Use larger/full profiles only when the card needs broader tools or 256k context.
- Qwen3.8 BF16 profiles: `qwen38-27b-uncensored-bf16-full-128k` keeps the full tool surface, while `qwen38-27b-uncensored-bf16-web-terminal-128k` is the restricted web/terminal profile. Both use LiteLLM model `qwen3.8-27b-uncensored-bf16` and the user service `llama-qwen38-uncensored-bf16.service` on `http://127.0.0.1:11439/v1`.
- Qwen3.8-Flash-Next status: not promoted on 2026-09-02. A side-by-side `llama-rocm-10.0-qwen38-flash-next` toolbox using llama.cpp build `10672` / commit `590ac45bc` was created and the AtomicChat `AD-4.27bpw-Q4_K_M-M64` split GGUF was downloaded and verified under `/mnt/ai/models/qwen38-flash-next-ad-4.27bpw-q4km-m64`. Isolated load attempts were killed by host RAM OOM before health, so the temporary service and LiteLLM route were removed. Do not retry without an owner-approved memory-layout change or a materially smaller higher-confidence candidate.
- LiteLLM split-port routing: `litellm-ollama-proxy.service` is the internal backend on `127.0.0.1:4004`; Hermes profiles use this loopback endpoint. `litellm-lan-auth-proxy.service` exposes the OpenAI-compatible API on `0.0.0.0:4000` for LAN clients such as Cline and requires a bearer key. The key is stored in OpenBao at `secret/homelab/providers/litellm`, field `lan_api_key`, with local runtime copy `/home/helios/.config/litellm/litellm-lan-api-key.env`. Cline should use base URL `http://192.168.1.123:4000/v1` and that key.
- LiteLLM package status: `/home/helios/.local/share/litellm/venv` was upgraded from LiteLLM `1.91.0` to `1.97.0` on 2026-08-18 after restoring `pip` in the venv. Freeze backups are under `/home/helios/.local/share/litellm/backups/`.
- ai-workstation monitoring: `node-exporter.service` exposes host metrics on `0.0.0.0:9100`; `ai-workstation-gpu-exporter.service` exposes ROCm/sysfs GPU metrics on `0.0.0.0:9101`. Prometheus scrapes both and the `LiteLLM / Hermes Usage` Grafana dashboard includes an `AI Workstation Health` section.
- Hermes dashboard: `hermes-dashboard.service` is enabled and bound to `127.0.0.1:9119` for SSH-tunneled browser access.
- Hermes dashboard browser sessions use a stable local session token from `/home/helios/.config/hermes-dashboard/session-token.env`, injected into `hermes-dashboard.service` by `/home/helios/.config/systemd/user/hermes-dashboard.service.d/50-stable-session-token.conf`. This prevents dashboard restarts from invalidating the browser chat websocket token. Do not print or commit the token value.
- Hermes OpenBao access: `hermes-gateway.service` and `hermes-dashboard.service` have OpenBao env injected through `20-openbao.conf` drop-ins using read-only policy `hermes-bootstrap-env-read`.
- Hermes OpenBao helper: `/home/helios/.local/bin/openbao-env-get FIELD_NAME` reads fields from `secret/homelab/bootstrap/env`, for example `openbao-env-get AI_WORKSTATION_PASSWORD`.

### Current model-specific profiles

| Profile | Purpose |
| --- | --- |
| `qwen3-coder-30b-a3b-q8_0-metered-64k` | Metered 64k local profile |
| `qwen3-coder-30b-a3b-q8_0-full-128k` | Full-tool 128k profile |
| `qwen3-coder-30b-a3b-q8_0-web-128k` | Restricted web-only profile |
| `qwen3-coder-30b-a3b-q8_0-worker-128k` | Lean implementation worker |
| `qwen3-coder-30b-a3b-q8_0-full-256k` | Full-tool large-context profile |
| `qwen38-27b-uncensored-q6_k-web-terminal-128k` | Preferred Q6 web and terminal profile |
| `qwen38-27b-uncensored-q6_k-discord-128k` | Restricted Discord route profile; root gateway owns the bot credential |
| `qwen38-27b-uncensored-bf16-full-128k` | Full-tool BF16 experiment profile |
| `qwen38-27b-uncensored-bf16-web-terminal-128k` | Restricted BF16 web and terminal profile |
| `qwen38-27b-obliterated-q6_k-full-128k` | Full-tool obliterated Q6 profile |
| `qwen38-27b-obliterated-q6_k-web-128k` | Restricted obliterated Q6 web profile |
| `qwen38-27b-obliterated-q6_k-web-terminal-128k` | Restricted obliterated Q6 web and terminal profile |

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
qwen3-coder-30b-a3b-q8_0-worker-128k tools list
qwen38-27b-uncensored-bf16-full-128k tools list
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

- `qwen38-27b-uncensored-q6_k-web-terminal-128k`: Q6 browser chat with web and terminal access.
- `qwen3-coder-30b-a3b-q8_0-web-128k`: faster lightweight browser chat and quick Q&A.
- Q6-backed `default` or a `qwen3-coder-30b-a3b-q8_0-full-<context>` profile: full development work where broad tools are expected.
- `qwen38-27b-uncensored-bf16-full-128k`: controlled BF16 experiments that need the full Hermes tool surface.

## Strix Halo Backend Source

Backend source of truth for ROCm/Vulkan llama.cpp toolboxes:

- GitHub: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote clone path on workstation: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox containers include `llama-rocm-7.2.2`, refreshed `llama-rocm-7.14`, `llama-rocm-7.14-q4`, `llama-rocm-10.0-qwen38-test`, and `llama-rocm-10.0-qwen38-flash-next`.
- Qwen3.8 BF16 runtime image: `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.14`
- Qwen3.8-Flash-Next experimental runtime image: `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-10.0-qwen-3.8-flash-next` (`sha256:d2067225019f61d39c6531322fff8469d67a9a4457c83ed50945b8dffdd818be` as tested on 2026-09-02).

## Script

- `scripts/sync-strix-halo-backend.ps1`
  - Pulls latest upstream repo on workstation
  - Ensures `llama-rocm-7.14` toolbox exists
  - Validates device visibility with `llama-cli --list-devices`

## Required `.env` Keys

- `AI_WORKSTATION_IP`
- `AI_WORKSTATION_USER`
- `AI_WORKSTATION_PASSWORD`
