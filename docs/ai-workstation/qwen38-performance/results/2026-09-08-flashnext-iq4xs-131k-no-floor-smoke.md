# Qwen3.8 Flash-Next OrcaRouter IQ4_XS 131k No-Floor Smoke

Tested: 2026-09-08 16:20-16:28 America/Chicago.

## Purpose

This run checked whether the current OrcaRouter `IQ4_XS` Flash-Next route can
load at 131k context on the observed 96 GiB VRAM / 31 GiB Linux RAM BIOS split.
The user explicitly allowed a no-RAM-floor load and accepted manual reboot risk
if the host deadlocked.

## Configuration

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Model source | `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, `IQ4_XS` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf` |
| Active service | `llama-qwen38-flashnext-iq4xs-131k-manual.service` |
| Durable 64k service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`, disabled and stopped before launch |
| Port | `11454` |
| Context | `131072` |
| Main flags | `-ngl 999 -c 131072 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |
| MTP | Disabled |
| Toolbox | `llama-rocm-10.0-qwen38-flash-next` |
| BIOS memory split | Observed 96 GiB VRAM / 31 GiB Linux RAM |
| RAM floor | None by user request |
| Autostart | Disabled for durable large model services; 131k test service is transient/manual |

## Load And Residency

| Measurement | Value |
| --- | ---: |
| Pre-load available RAM after unload | 26010 MiB |
| Pre-load swap used after unload | 2478 MiB |
| Pre-load VRAM used after unload | 757325824 bytes |
| Pre-load model state | `ollama ps` empty; previous 64k `llama-server` stopped |
| Health time | 173 seconds |
| Minimum available RAM during load | 465 MiB |
| Maximum swap used during load | 39571 MiB |
| Maximum observed VRAM during load | 72233414656 bytes |
| Post-smoke available RAM | 10816 MiB |
| Post-smoke swap used | 20321 MiB |
| Post-smoke VRAM used | 72277131264 bytes |
| Server-reported context | `n_ctx=131072`, `n_ctx_train=262144` |

## Smoke Results

| Endpoint | Result |
| --- | --- |
| Direct llama.cpp health | `{"status":"ok"}` |
| Direct llama.cpp sentinel chat | Passed with `IQ4XS_131K_OK` |
| LiteLLM model metadata | `max_input_tokens=131072` |
| LiteLLM sentinel chat | Passed with `LITELLM_IQ4XS_131K_OK` |
| Hermes global default | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`, `model.context_length=131072` |
| Hermes Discord profile | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`, `model.context_length=131072` |

## Interpretation

The 131k IQ4_XS route loaded and passed direct plus LiteLLM smoke on the current
96 GiB VRAM split. The steady-state VRAM increase over the 64k route was modest
in this smoke test, rising from roughly 70.9 GB to roughly 72.3 GB decimal VRAM.

The load phase remains the limiting risk. Available system RAM dropped to only
465 MiB and swap reached about 39.6 GiB before the service became healthy. This
is a supervised manual-test configuration only, not a boot-time or unattended
default. No controlled Python telemetry quality benchmark was run for the 131k
configuration during this smoke.
