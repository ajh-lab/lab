You are operating or recovering the Fedora AI workstation (`ai-workstation-evox2`,
`helios@192.168.1.123`) from the Windows lab workspace.

## CURRENT OPERATIONAL CONTEXT

Last verified: 2026-09-08 08:35 America/Chicago.

Start with the root lab `ai-baseline-context.md`, then use:

- `automation/ai-workstation/README.md` for the service/runbook view.
- `docs/ai-workstation/qwen38-performance/model-comparison.md` for the model
  decision table.
- `docs/ai-workstation/qwen38-performance/results/` for timestamped benchmark
  reports and generated artifacts.

Current Hermes experimental manual-test default:

- Model alias: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`
- Service: `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`
- llama.cpp route: `http://127.0.0.1:11454/v1`
- LiteLLM route: `http://127.0.0.1:4004/v1`
- Context: `65536`
- Runtime: Flash-Next ROCm toolbox `llama-rocm-10.0-qwen38-flash-next`
- Runtime flags: `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui`
- Model files: `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs`
- Host memory split during current test: observed 96 GiB VRAM / 31 GiB Linux
  RAM, with disk-backed swap persisted at `/mnt/ai/swap/qwen-flashnext-test.swap`.
- Guardrail: the current IQ4_XS full-offload route reproduced the 17/18
  repaired score, but startup is still dangerous. The 2026-09-08 reload reached
  health after 193 seconds, with only 518 MiB minimum available RAM and 39897
  MiB maximum swap used during load. The service is active now for manual Hermes
  testing, but all large llama.cpp model services should stay disabled for
  autostart.
- Previous 64 GiB VRAM split during test: observed 64 GiB VRAM / 62 GiB Linux
  RAM, with disk-backed swap persisted at `/mnt/ai/swap/qwen-flashnext-test.swap`.
- Previous 64 GiB split guardrail: the IQ4_XS test had no available-RAM floor. Full offload
  failed at 64k with a ROCm KV-cache OOM on the 64 GiB VRAM split, so the active
  service temporarily used fit mode. The successful fit-mode load reached health after 119
  seconds, with 8054 MiB minimum available RAM and 28299 MiB maximum swap used
  during load.
- Current residency expectation: only IQ4_XS should be resident for normal
  manual testing. `ollama ps` should remain empty before controlled Flash-Next
  tests.

Current controlled-quality rollback:

- Model alias: `qwen3.8-27b-uncensored-orcarouter-q4_k_m`
- Service: `llama-qwen38-orcarouter-uncensored-q4km.service`
- llama.cpp route: `http://127.0.0.1:11448/v1`
- Context: `131072`
- Controlled benchmark score: 14/18 first pass, 17/18 repaired.

Flash-Next IQ3_M 64k benchmark on 2026-09-07:

- Controlled benchmark score: 13/18 first pass, 15/18 repaired.
- Telemetry generation speed: 26.71 tok/s first pass, 24.39 tok/s repair.
- Runtime tuning: changing to `--repeat-penalty 1.0` kept the same
  13/18 -> 15/18 score and improved telemetry speed to 27.58 tok/s first pass
  and 25.24 tok/s repair.
- Prompt-side tuning: a strict Python contract-audit system prompt improved
  the controlled score to 14/18 first pass and 16/18 repaired. This prompt is
  not yet globally applied to Hermes.
- Rejected tuning: unbounded `--reasoning on` produced invalid length-capped
  outputs, and `--reasoning-budget 512` introduced a hidden `fix="none"`
  regression.
- Short standard coding smokes: about 22.72-23.38 tok/s.
- Detailed report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq3m-64k-python-telemetry-eval.md`
- Runtime tuning report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq3m-runtime-tuning-eval.md`
- Config sweep report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-iq3m-config-sweep-eval.md`
- Config sweep summary: explicit thread settings did not materially beat the
  live runtime; larger `-b/-ub` settings were slightly faster but repaired to
  only 14/18; `--fit on --fit-target 1536` and
  `--cache-ram 32768 --kv-unified --ctx-checkpoints 64` did not help this
  benchmark. `ngram-mod` speculative decoding preserved the 13/18 -> 15/18
  score and improved the long repair generation to 54.51 tok/s, but did not
  improve short benchmark prompts broadly and is not yet promoted as the live
  default.

Post-BIOS Flash-Next IQ3_M 64k 4 GiB-floor test on 2026-09-08:

- Loaded successfully on the observed 64 GiB VRAM / 62 GiB Linux RAM split after
  lowering the startup floor from 8 GiB to 4 GiB.
- Minimum available RAM during load: 4535 MiB; after the controlled benchmark,
  about 28630 MiB remained available with about 2164 MiB swap used.
- Loaded VRAM after the controlled benchmark: 62703439872 bytes.
- Standard benchmark: 26.39 tok/s on `rust-light`, 25.99 tok/s on
  `code-review`.
- Controlled benchmark score: 12/18 first pass, 13/18 repaired.
- Telemetry generation speed: 27.68 tok/s first pass, 23.67 tok/s repair.
- During that test, Hermes default and the legacy Discord profile temporarily
  pointed at `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` with 64k context.
- Detailed report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq3m-64k-post-bios-floor4g.md`

Flash-Next IQ4_XS 64k benchmark on 2026-09-07:

- Model alias: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`.
- Source: `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, `IQ4_XS`, 91 GiB
  on disk under `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs`.
- Service: `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`, port
  `11454`, 64k context, no MTP.
- Loaded VRAM: about 71.1 GB decimal.
- Controlled benchmark score: 13/18 first pass, 17/18 repaired.
- Telemetry generation speed: 26.92 tok/s first pass, 24.88 tok/s repair.
- Clean confirmation with `ollama ps` empty reproduced 13/18 first pass and
  17/18 repaired, with 27.24 tok/s first pass and 25.41 tok/s repair.
- After the workstation returned to the observed 96 GiB VRAM / 31 GiB Linux RAM
  split on 2026-09-08, an original-flags retest again scored 13/18 first pass
  and 17/18 repaired, with 26.18 tok/s first pass and 25.24 tok/s repair.
  Startup reached health after 193 seconds, but dropped to only 518 MiB
  available RAM and used 39897 MiB swap.
- Strict system prompt retest scored 14/18 first pass but only 14/18 repaired,
  so do not apply that strict prompt globally to IQ4_XS.
- The only repaired standards failure was lowercase RFC3339 `t`/`z`, matching
  the 27B OrcaRouter Q4_K_M remaining defect.
- IQ4_XS is now the current Hermes experimental manual-test default; the
  legacy Discord profile route was also updated to this alias.
- Detailed report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq4xs-64k-python-telemetry-eval.md`
- Clean confirmation report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-07-flashnext-orcarouter-iq4xs-64k-clean-confirmation.md`

Post-BIOS Flash-Next IQ4_XS 64k fit/no-floor test on 2026-09-08:

- On the observed 64 GiB VRAM / 62 GiB Linux RAM split, full offload with
  `-ngl 999` failed before health because llama.cpp filled VRAM and could not
  allocate another 816 MiB ROCm buffer for KV cache.
- Removing explicit `-ngl` and using `--fit on --fit-target 1536` reached
  health after 119 seconds.
- Load-time minimum available RAM: 8054 MiB. Load-time maximum swap used:
  28299 MiB.
- After the controlled benchmark, about 30618 MiB RAM remained available, about
  9386 MiB swap was used, and ROCm VRAM allocation was 67059216384 bytes.
- Standard benchmark: 24.22 tok/s on `rust-light`, 23.73 tok/s on
  `code-review`.
- Controlled benchmark score: 12/18 first pass, 13/18 repaired.
- Telemetry generation speed: 25.66 tok/s first pass, 22.73 tok/s repair.
- During that test, Hermes default and the legacy Discord profile pointed at
  `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` with 64k context.
- Detailed report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq4xs-64k-fit-no-floor.md`

Post-revert Flash-Next IQ4_XS 64k original-flags test on 2026-09-08:

- After returning the BIOS split to observed 96 GiB VRAM / 31 GiB Linux RAM,
  IQ4_XS was reloaded with the original full-offload flags:
  `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui`.
- Load-time minimum available RAM: 518 MiB. Load-time maximum swap used:
  39897 MiB. Health time: 193 seconds.
- Post-load state: exactly one `llama-server`, `ollama ps` empty, about
  70864687104 bytes VRAM used, and the IQ4_XS service disabled for autostart
  while left active for manual Hermes testing.
- Standard benchmark: 24.78 tok/s on `rust-light`, 24.34 tok/s on
  `code-review`.
- Controlled benchmark score: 13/18 first pass, 17/18 repaired.
- Telemetry generation speed: 26.18 tok/s first pass, 25.24 tok/s repair.
- Detailed report:
  `docs/ai-workstation/qwen38-performance/results/2026-09-08-flashnext-iq4xs-96gb-original-flags-64k.md`

Hermes Discord and OpenBao status on 2026-09-07:

- The legacy Discord profile `qwen38-27b-uncensored-q6_k-discord-128k`
  points at `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`.
- Actual outbound delivery to `discord:helios` returned `sent`, and the
  profile smoke returned `DISCORD_ROUTE_OK`.
- OpenBao policy `hermes-bootstrap-env-read` was updated for the documented
  KV v2 bootstrap path, and the workstation Hermes/OpenBao token was rotated.
  `openbao-env-get AI_WORKSTATION_PASSWORD >/dev/null` now succeeds without
  printing the secret, and the running `hermes-gateway.service` process has
  `SUDO_PASSWORD` present in its environment.

Record every future model experiment with:

- timestamp and timezone
- model source, quantization, file path, service name, port, context, MTP status
- active BIOS/UMA memory split, Linux RAM/swap, loaded VRAM
- Hermes, LiteLLM, llama.cpp, ROCm, OS, and kernel versions
- direct health, LiteLLM model discovery, smoke tests, controlled benchmark score
- rollback service and config backup path
- Discord route status, because the `@Helios` bot can keep using a profile name
  that points at an old stopped model backend

---

The original fresh-install setup notes follow. Use them only when rebuilding the
host from scratch.

You are configuring a freshly installed Fedora Workstation system into a secure, headless AI workstation accessible from a Windows client over SSH.

## OBJECTIVE

Build a fully functional AI node that:

* Uses secure SSH key-based access from a Windows machine
* Runs local LLMs (Ollama + llama.cpp)
* Supports agent-based automation
* Supports voice interaction
* Stores all AI data on a dedicated mounted drive
* Is stable, reproducible, and safe (no lockouts)

---

## SYSTEM CONTEXT

### Remote Client:

* Windows machine using OpenSSH (PowerShell)

### Target Machine:

* Fedora Workstation (fresh install)
* SSH already enabled
* User has sudo privileges
* Secondary NVMe exists for AI data

---

## CRITICAL SAFETY RULES

* DO NOT disable SSH password authentication until key-based login is confirmed working
* DO NOT reboot unless necessary
* DO NOT modify system boot configuration
* ALWAYS validate connectivity before making access changes

---

## EXECUTION PLAN

### 1. VERIFY NETWORK + SSH

* Confirm SSH is running:
  systemctl status sshd
* Confirm firewall allows SSH:
  firewall-cmd --list-services
* If missing, add:
  firewall-cmd --add-service=ssh --permanent
  firewall-cmd --reload

---

### 2. SET UP SSH KEY AUTH (WINDOWS CLIENT COMPATIBLE)

Assume user generated key on Windows already:

* Public key located at:
  C:\Users<user>.ssh\id_rsa.pub OR id_ed25519.pub

On Fedora:

* Ensure directory:
  mkdir -p ~/.ssh
  chmod 700 ~/.ssh

* Append public key to:
  ~/.ssh/authorized_keys

* Set permissions:
  chmod 600 ~/.ssh/authorized_keys

---

### 3. VALIDATE SSH KEY LOGIN

* Instruct user to open a NEW Windows PowerShell session and run:
  ssh <username>@<fedora-ip>

* WAIT until user confirms passwordless login works

---

### 4. HARDEN SSH

ONLY AFTER CONFIRMATION:

Edit:
/etc/ssh/sshd_config

Set:
PasswordAuthentication no

Then:
systemctl restart sshd

---

### 5. SYSTEM PREP

* Update system:
  dnf update -y

* Install essentials:
  dnf install -y git curl wget htop btop tmux neovim gcc make cmake python3 python3-pip

---

### 6. STORAGE CONFIGURATION

* Detect secondary NVMe via:
  lsblk

* If unformatted:
  mkfs.ext4 /dev/<device>

* Mount:
  mkdir -p /mnt/ai
  mount /dev/<device> /mnt/ai

* Persist in /etc/fstab

* Create structure:
  /mnt/ai/models
  /mnt/ai/ollama
  /mnt/ai/llama
  /mnt/ai/qdrant
  /mnt/ai/docker
  /mnt/ai/logs

---

### 7. INSTALL OLLAMA

* Install Ollama

* Configure model storage path:
  export OLLAMA_MODELS=/mnt/ai/ollama

* Ensure service runs on boot

* Test:
  ollama run mistral

---

### 8. INSTALL LLAMA.CPP

* Clone repo

* Build with:

  * Vulkan support
  * CPU optimizations

* Install binary system-wide

* Validate with test model

---

### 9. GPU DETECTION + BACKEND

* Detect AMD GPU
* Attempt Vulkan backend first
* If ROCm unavailable or unstable → continue with Vulkan

---

### 10. VECTOR DATABASE

* Install Qdrant (Docker preferred)
* Store data in:
  /mnt/ai/qdrant
* Ensure persistence

---

### 11. VOICE STACK

Install:

* faster-whisper OR whisper.cpp
* Piper TTS

Validate:

* STT works from audio file
* TTS produces output audio

---

### 12. AGENT FRAMEWORK

* Install OpenClaw (or similar lightweight agent framework)
* Configure:

  * Uses local Ollama endpoint
  * Supports tool calling
  * Has filesystem + shell tools

---

### 13. TOOLING LAYER

Create structured tools:

* shell execution (restricted)
* file read/write
* system info
* optional: docker

---

### 14. SERVICE MANAGEMENT

Ensure on boot:

* Ollama
* Qdrant
* Agent runtime (if daemonized)

Use systemd where appropriate

---

### 15. LOGGING

Centralize logs in:
/mnt/ai/logs

---

### 16. OPTIONAL WEB UI

Attempt:
dnf install cockpit
systemctl enable --now cockpit.socket

If inaccessible:

* Check firewall
* Log issue
* DO NOT block setup

---

## FINAL OUTPUT

Provide:

* Summary of installed components
* Active services
* Storage layout
* Model readiness
* Any warnings or incomplete steps

---

## EXECUTION STYLE

* Proceed step-by-step
* Validate each step
* Be resilient to failure
* Prefer stability over experimentation

END TASK
