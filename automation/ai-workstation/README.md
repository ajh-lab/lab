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
- Hermes status: `hermes-gateway.service` is enabled and active (`Hermes Agent v0.21.0 / 2026.8.31`, upstream `1cd9106e`, verified up to date on 2026-09-06), with systemd linger enabled. The 2026-09-06 update migrated Hermes config format from v39 to v41 and synced bundled skills across profiles.
- Stable Q4 rollback from the earlier 2026-09-07 tests: `qwen3.8-27b-uncensored-orcarouter-q4_k_m` routes through local LiteLLM (`http://127.0.0.1:4004/v1`) and llama.cpp on `http://127.0.0.1:11448/v1` with 131k context. It passed direct health plus LiteLLM smoke after the Flash-Next service experiments. `UD-IQ3_XXS` on port `11455` remains the safer 8 GiB-floor Flash-Next fallback.
- Current Flash-Next manual test default as of 2026-09-08: after returning the BIOS split to observed 96 GiB VRAM / 31 GiB Linux RAM, `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` is loaded on `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` / port `11454` with 64k context, full offload, and the original successful flags `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui`. It reached health after 193 seconds, but startup dipped to 518 MiB available RAM and used up to about 39.9 GiB swap. It passed direct and LiteLLM smoke, reproduced 13/18 first pass and 17/18 repaired on the controlled telemetry benchmark, and produced 26.18 tok/s first / 25.24 tok/s repair. Keep all large model services disabled for autostart; this is a supervised manual default. `qwen3.8-27b-uncensored-orcarouter-q4_k_m` remains the lower-VRAM quality rollback and `UD-IQ3_XXS` remains the safer Flash-Next fallback.
- Hermes DeepSeek profiles are model-named: `deepseek-v4-flash` and `deepseek-v4-pro`. Do not recreate the removed legacy `deepseek` profile. The DeepSeek key is stored in OpenBao at `secret/homelab/providers/deepseek`, field `api_key`; runtime fallback `.env` files must not be printed or committed.
- Hermes model alias source: `qwen3-coder:30b-a3b-q8_0`; aliases exist for `hermes-qwen3-coder:30b-64k`, `hermes-qwen3-coder:30b-128k`, and `hermes-qwen3-coder:30b-256k`. As of 2026-09-07, the LiteLLM routes for those aliases set `keep_alive: 0s` so incidental qwen-coder calls do not keep a 39+ GB Ollama model resident in VRAM during Flash-Next testing.
- Hermes browser chat latency note: the 256k default increases KV-cache allocation but fits the Strix Halo ROCm memory budget. Full tool-enabled Hermes chat is still mostly prompt/tool overhead and can loop on lightweight questions. For direct browser chat, prefer `qwen3-coder-128k-fast-chat` or `qwen3-coder-256k-fast-chat`; those profiles restrict CLI tools to web only, disable local action tools, set `agent.max_turns: 4`, and disable environment probing.
- Hermes Discord route note: the legacy profile name `qwen38-27b-uncensored-q6_k-discord-128k` is still used by the `@Helios` Discord bot path. It currently points at `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` through LiteLLM with 64k context; this was verified from the profile config on 2026-09-08 after the 96 GiB VRAM original-flags reload. Backups include `/home/helios/.hermes/profiles/qwen38-27b-uncensored-q6_k-discord-128k/config.yaml.bak-flashnext-route-20260907-133709`, `/home/helios/.hermes/backups/promote-flashnext-iq4xs-20260907-180340/discord-profile-config.yaml`, and `/home/helios/.hermes/backups/restore-q4-after-iq3m-131k-20260907-221857/discord-profile-config.yaml`. Actual outbound delivery to `discord:helios` returned `sent` on 2026-09-07, and the profile smoke returned `DISCORD_ROUTE_OK` then.
- Hermes Kanban worker profile: `qwen3-coder-128k-worker` is the preferred local worker for normal coding cards. It uses `hermes-qwen3-coder:30b-128k`, keeps only terminal/file/code-execution/todo/skills tools, disables browser/image/TTS/computer-use/delegation/cron/memory extras, sets `agent.max_turns: 28`, sets `agent.reasoning_effort: none` so Ollama does not receive unsupported thinking requests, and disables environment probing with a fixed lab workspace hint. Use larger/full profiles only when the card needs broader tools or 256k context.
- Qwen3.8 BF16 tool-enabled test profile: `qwen38bf16tools` uses LiteLLM model `qwen3.8-27b-bf16`, alias `/home/helios/.local/bin/qwen38-bf16-tools`, and the user service `llama-qwen38-bf16.service` on `http://127.0.0.1:11437/v1`. The model file came from Ollama tag `qwen3.8:27b-bf16` and is stored under `/mnt/ai/ollama-qwen38/models`; Ollama `0.32.14` can download/show the model but was not the working runtime because it under-offloaded this dense BF16 model on Strix Halo and hit system-memory OOM. Use the refreshed `llama-rocm-7.14` toolbox for this model. The profile keeps Hermes' full default tool surface enabled; web search still requires a configured Hermes search/tool-gateway API key. Existing Custom endpoint model picker lists include the qwen3-coder aliases, both DeepSeek models, and `qwen3.8-27b-bf16`.
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
