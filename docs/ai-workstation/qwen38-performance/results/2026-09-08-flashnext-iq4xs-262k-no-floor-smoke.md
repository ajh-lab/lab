# Qwen3.8 Flash-Next OrcaRouter IQ4_XS 262k No-Floor Smoke

Tested: 2026-09-08 16:33-16:39 America/Chicago.

## Purpose

This run checked whether the current OrcaRouter `IQ4_XS` Flash-Next route can
load at the model's full 262k trained context on the observed 96 GiB VRAM /
31 GiB Linux RAM BIOS split. The run followed the previous no-RAM-floor manual
test pattern.

## Configuration

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Model source | `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, `IQ4_XS` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf` |
| Active service | `llama-qwen38-flashnext-iq4xs-262k-manual.service` |
| Previous test service | `llama-qwen38-flashnext-iq4xs-131k-manual.service`, stopped before launch |
| Durable 64k service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`, disabled and stopped before launch |
| Port | `11454` |
| Context | `262144` |
| Main flags | `-ngl 999 -c 262144 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |
| MTP | Disabled |
| Toolbox | `llama-rocm-10.0-qwen38-flash-next` |
| BIOS memory split | Observed 96 GiB VRAM / 31 GiB Linux RAM |
| RAM floor | None |
| Autostart | Disabled for durable large model services; 262k test service is transient/manual |

## Load And Residency

| Measurement | Value |
| --- | ---: |
| Pre-load available RAM after unload | 26406 MiB |
| Pre-load swap used after unload | 2802 MiB |
| Pre-load VRAM used after unload | 767868928 bytes |
| Pre-load model state | `ollama ps` empty; previous 131k `llama-server` stopped |
| Health time | 161 seconds |
| Minimum available RAM during load | 385 MiB |
| Maximum swap used during load | 39340 MiB |
| Maximum observed VRAM during load | 74922102784 bytes |
| Post-smoke available RAM | 11316 MiB |
| Post-smoke swap used | 20189 MiB |
| Post-smoke VRAM used | 74955206656 bytes |
| Server-reported context | `n_ctx=262144`, `n_ctx_train=262144` |

## Smoke Results

| Endpoint | Result |
| --- | --- |
| Direct llama.cpp health | `{"status":"ok"}` |
| Direct llama.cpp metadata | `n_ctx=262144`, `n_ctx_train=262144` |
| Direct llama.cpp sentinel chat | Passed with `IQ4XS_262K_OK` |
| LiteLLM model metadata | `max_input_tokens=262144` |
| LiteLLM sentinel chat | Passed with `LITELLM_IQ4XS_262K_OK` |
| Hermes global default | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`, `model.context_length=262144` |
| Hermes Discord profile | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`, `model.context_length=262144` |

## Interpretation

The 262k IQ4_XS route loaded and passed direct plus LiteLLM smoke on the current
96 GiB VRAM split. This confirms the model can run at its full trained context
on the workstation when only one large model is resident.

The load phase is still the limiting risk. Available system RAM dropped to only
385 MiB and swap reached about 39.3 GiB before the service became healthy. This
is a supervised manual-test configuration only, not a boot-time or unattended
default. No controlled Python telemetry quality benchmark was run for the 262k
configuration during this smoke.

Backups:

- LiteLLM: `/home/helios/.config/litellm/backups/iq4xs-262k-20260908-163726`
- Hermes: `/home/helios/.hermes/backups/iq4xs-262k-context-20260908-163726`
