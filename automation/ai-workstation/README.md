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
- Hermes status: `hermes-gateway.service` is enabled and active (`Hermes Agent v0.21.1 / 2026.9.7`, upstream `a529ecfe`, verified up to date on 2026-09-08), with systemd linger enabled. The 2026-09-06 update migrated Hermes config format from v39 to v41 and synced bundled skills across profiles; the 2026-09-08 update synced bundled skills across active profiles and restarted `hermes-gateway.service` plus `hermes-dashboard.service`.
- Stable Q4 rollback from the earlier 2026-09-07 tests: `qwen3.8-27b-uncensored-orcarouter-q4_k_m` routes through local LiteLLM (`http://127.0.0.1:4004/v1`) and llama.cpp on `http://127.0.0.1:11448/v1` with 131k context. It passed direct health plus LiteLLM smoke after the Flash-Next service experiments. `UD-IQ3_XXS` on port `11455` remains the safer 8 GiB-floor Flash-Next fallback.
- Current Flash-Next manual test default as of 2026-09-08: after returning the BIOS split to observed 96 GiB VRAM / 31 GiB Linux RAM, `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` is loaded on `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` / port `11454` with 64k context, full offload, and the original successful flags `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui`. It reached health after 193 seconds, but startup dipped to 518 MiB available RAM and used up to about 39.9 GiB swap. It passed direct and LiteLLM smoke, reproduced 13/18 first pass and 17/18 repaired on the controlled telemetry benchmark, and produced 26.18 tok/s first / 25.24 tok/s repair. Keep all large model services disabled for autostart; this is a supervised manual default. `qwen3.8-27b-uncensored-orcarouter-q4_k_m` remains the lower-VRAM quality rollback and `UD-IQ3_XXS` remains the safer Flash-Next fallback.
- Hermes DeepSeek profiles are model-named: `deepseek-v4-flash` and `deepseek-v4-pro`. Do not recreate the removed legacy `deepseek` profile. The DeepSeek key is stored in OpenBao at `secret/homelab/providers/deepseek`, field `api_key`; runtime fallback `.env` files must not be printed or committed.
- Hermes model alias source: `qwen3-coder:30b-a3b-q8_0`; aliases exist for `hermes-qwen3-coder:30b-64k`, `hermes-qwen3-coder:30b-128k`, and `hermes-qwen3-coder:30b-256k`. As of 2026-09-07, the LiteLLM routes for those aliases set `keep_alive: 0s` so incidental qwen-coder calls do not keep a 39+ GB Ollama model resident in VRAM during Flash-Next testing.
- Hermes profile naming: model-specific profiles use `<model>-<variant>-<role>-<context>`, with the context window last. Do not recreate the removed `-fast-chat` names. Use `qwen38-27b-uncensored-q6_k-web-terminal-128k` for Q6 browser chat with terminal access or `qwen3-coder-30b-a3b-q8_0-web-128k` for faster web-only chat.
- Hermes update recovery: the 2026-09-01 update from `v0.20.5` to `v0.21.0` created the full restore archive `/home/helios/.hermes/backups/pre-update-2026-09-01-223739.zip`. The prior local Kanban heartbeat/dashboard patch remains intentionally parked as git stash `hermes-update-autostash-20260902-033801` and as `/home/helios/.hermes/backups/hermes-update-20260902T033737Z/local-source-changes.patch`; do not reapply it blindly because upstream now contains a substantially expanded heartbeat and stale-worker implementation.
- Hermes Discord route note: the legacy profile name `qwen38-27b-uncensored-q6_k-discord-128k` is still used by the `@Helios` Discord bot path. It currently points at `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` through LiteLLM with 64k context; this was verified from the profile config on 2026-09-08 after the 96 GiB VRAM original-flags reload. Backups include `/home/helios/.hermes/profiles/qwen38-27b-uncensored-q6_k-discord-128k/config.yaml.bak-flashnext-route-20260907-133709`, `/home/helios/.hermes/backups/promote-flashnext-iq4xs-20260907-180340/discord-profile-config.yaml`, and `/home/helios/.hermes/backups/restore-q4-after-iq3m-131k-20260907-221857/discord-profile-config.yaml`. Actual outbound delivery to `discord:helios` returned `sent` on 2026-09-07, and the profile smoke returned `DISCORD_ROUTE_OK` then.
- Hermes Kanban worker profile: `qwen3-coder-30b-a3b-q8_0-worker-128k` is the preferred qwen3-coder worker for normal coding cards. It uses `hermes-qwen3-coder:30b-128k`, keeps only terminal/file/code-execution/todo/skills tools, disables browser/image/TTS/computer-use/delegation/cron/memory extras, sets `agent.max_turns: 28`, sets `agent.reasoning_effort: none` so Ollama does not receive unsupported thinking requests, and disables environment probing with a fixed lab workspace hint. Use larger/full profiles only when the card needs broader tools or 256k context.
- Qwen3.8 BF16 profiles: `qwen38-27b-uncensored-bf16-full-128k` keeps the full tool surface, while `qwen38-27b-uncensored-bf16-web-terminal-128k` is the restricted web/terminal profile. Both use LiteLLM model `qwen3.8-27b-uncensored-bf16` and the user service `llama-qwen38-uncensored-bf16.service` on `http://127.0.0.1:11439/v1`.
- Qwen3.8 Q6_K MTP test route: `qwen3.8-27b-uncensored-q6_k-mtp` uses target GGUF `/mnt/ai/models/qwen38-uncensored-q6k/Qwen3.8-27B-Uncensored-Q6_K.gguf` with draft GGUF `/mnt/ai/models/qwen38-uncensored-q4km-mtp-draft/Qwen3.8-27B-Uncensored-draft-Q4_0.gguf`, service `llama-qwen38-uncensored-q6k-mtp.service`, port `11450`, and 64k context. It passed health/LiteLLM/Hermes smoke on 2026-09-05, but scored only 5/18 first pass and 6/18 repaired on the controlled Python telemetry benchmark. It is stopped/disabled; treat it as a rejected speed experiment, not as a quality baseline.
- Qwen3.8 64k comparison routes: `qwen3.8-27b-uncensored-q6_k-64k` (`llama-qwen38-uncensored-q6k-64k.service`, port `11451`) and `qwen3.8-27b-uncensored-orcarouter-q4_k_m-64k` (`llama-qwen38-orcarouter-uncensored-q4km-64k.service`, port `11452`) were created on 2026-09-05 as test routes. Both matched their 131k controlled benchmark scores at 64k: Q6_K stayed 14/18 first and 16/18 repaired, while OrcaRouter Q4_K_M stayed 14/18 first and 17/18 repaired. The 64k routes are available through LiteLLM as test routes; the 131k OrcaRouter Q4_K_M alias remains the best controlled-quality rollback while Flash-Next is under manual evaluation.
- Qwen3.8 Flash-Next OrcaRouter IQ3_M test route: `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` uses split GGUF files under `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq3m`, service file `llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service`, port `11453`, and the Flash-Next ROCm toolbox `llama-rocm-10.0-qwen38-flash-next`. It required disk-backed swap on the earlier 30 GiB system-RAM split; `/mnt/ai/swap/qwen-flashnext-test.swap` is persisted in `/etc/fstab` with `nofail,x-systemd.requires-mounts-for=/mnt/ai`. On 2026-09-07 it passed 64k direct llama.cpp and LiteLLM smoke, scored 13/18 first pass and 15/18 repaired on the controlled Python telemetry benchmark, and produced 26.71 tok/s first generation / 24.39 tok/s repair generation. A repeat-penalty 1.0 retest kept the same 13/18 -> 15/18 score while improving telemetry speed to 27.58 tok/s first / 25.24 tok/s repair. A 131k transient manual load reached health and passed smoke, but the later always-on service transition was not accepted after VRAM pressure and AMDGPU/OOM evidence. A later guarded retry after unloading Q4 found that 131k, 64k, and 16k service starts all dropped below the requested 12 GiB available system-RAM floor before health. After the BIOS split changed to observed 64 GiB VRAM / 62 GiB Linux RAM, a 64k retry with an 8 GiB available-RAM floor still dropped to about 5541 MiB available before health and was guard-stopped. Keep IQ3_M manual-only; do not enable it at login boot. Detailed results are in `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq3m-64k-python-telemetry-eval.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq3m-runtime-tuning-eval.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq3m-config-sweep-eval.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq3m-131k-manual-test.md`, and `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq3m-64k-post-bios-ram-floor.md`.
- Qwen3.8 Flash-Next OrcaRouter IQ4_XS test route: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` uses split GGUF files under `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs`, service `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`, port `11454`, and 64k context. It uses the Flash-Next ROCm toolbox, full offload on the 96 GiB VRAM split, no MTP, and the original successful `-b 1024 -ub 256` batch settings. The model directory is 91 GiB and loaded VRAM is about 70.9-71.1 GB decimal. On 2026-09-07 it scored 13/18 first pass and 17/18 repaired, produced 26.92 tok/s first generation and 24.88 tok/s repair generation, and a clean confirmation with `ollama ps` empty reproduced 13/18 first and 17/18 repaired at 27.24 tok/s first and 25.41 tok/s repair. On 2026-09-08, after returning to the 96 GiB VRAM split and original flags, it again scored 13/18 first and 17/18 repaired at 26.18 tok/s first and 25.24 tok/s repair. Startup still drove available RAM down to 518 MiB and swap up to about 39.9 GiB, so treat IQ4_XS as a supervised manual experiment only and keep autostart disabled. Detailed results are in `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq4xs-64k-python-telemetry-eval.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq4xs-64k-clean-confirmation.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq4xs-current-split-stability.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq4xs-clean-slate-ram-floor.md`, `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq4xs-64k-fit-no-floor.md`, and `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq4xs-96gb-original-flags-64k.md`.
- LiteLLM split-port routing: `litellm-ollama-proxy.service` is the internal backend on `127.0.0.1:4004`; Hermes profiles use this loopback endpoint. `litellm-lan-auth-proxy.service` exposes the OpenAI-compatible API on `0.0.0.0:4000` for LAN clients such as Cline and requires a bearer key. The key is stored in OpenBao at `secret/homelab/providers/litellm`, field `lan_api_key`, with local runtime copy `/home/helios/.config/litellm/litellm-lan-api-key.env`. Cline should use base URL `http://192.168.1.123:4000/v1` and that key. Backup before qwen-coder keep-alive was disabled: `/home/helios/.config/litellm/backups/disable-qwen-coder-keepalive-20260907-222450/config.yaml`.
- LiteLLM package status: `/home/helios/.local/share/litellm/venv` was upgraded from LiteLLM `1.91.0` to `1.97.0` on 2026-08-18 after restoring `pip` in the venv. Freeze backups are under `/home/helios/.local/share/litellm/backups/`.
- ai-workstation monitoring: `node-exporter.service` exposes host metrics on `0.0.0.0:9100`; `ai-workstation-gpu-exporter.service` exposes ROCm/sysfs GPU metrics on `0.0.0.0:9101`. Prometheus scrapes both and the `LiteLLM / Hermes Usage` Grafana dashboard includes an `AI Workstation Health` section.
- Hermes dashboard: `hermes-dashboard.service` is enabled and bound to `127.0.0.1:9119` for SSH-tunneled browser access.
- Hermes dashboard browser sessions use a stable local session token from `/home/helios/.config/hermes-dashboard/session-token.env`, injected into `hermes-dashboard.service` by `/home/helios/.config/systemd/user/hermes-dashboard.service.d/50-stable-session-token.conf`. This prevents dashboard restarts from invalidating the browser chat websocket token. Do not print or commit the token value.
- Hermes OpenBao access: `hermes-gateway.service` and `hermes-dashboard.service` have OpenBao env injected through `20-openbao.conf` drop-ins using read-only policy `hermes-bootstrap-env-read`. On 2026-09-07 the policy was updated for the documented KV v2 bootstrap path and the workstation token was rotated after `openbao-env-get AI_WORKSTATION_PASSWORD` returned 403.
- Hermes OpenBao helper: `/home/helios/.local/bin/openbao-env-get FIELD_NAME` reads fields from `secret/homelab/bootstrap/env`, for example `openbao-env-get AI_WORKSTATION_PASSWORD`. Current validation: the helper succeeds without printing the secret, and the running `hermes-gateway.service` process has `SUDO_PASSWORD` present.

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
systemctl --user status llama-qwen38-uncensored-bf16.service
curl -sS http://127.0.0.1:11439/health
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
