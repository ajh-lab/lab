# Qwen3.8 Flash-Next OrcaRouter IQ3_M 64k Post-BIOS RAM-Floor Test

Date: 2026-09-08 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Retest the OrcaRouter `IQ3_M` Flash-Next quant at 64k context after changing
the BIOS split from the earlier 32 GiB system RAM / 96 GiB VRAM setup to an
observed 64 GiB VRAM / 62 GiB Linux RAM setup.

This run used the operator-approved 8 GiB available-RAM floor.

## Runtime

| Field | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq3m/Qwen3.8-Flash-Next-Uncensored-IQ3_M-00001-of-00002.gguf` |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service` |
| Port | `11453` |
| Runtime | `llama-server` inside `llama-rocm-10.0-qwen38-flash-next` toolbox |
| Context | `65536` |
| Main flags | `-ngl 999 -c 65536 -b 512 -ub 128 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |

## Load Result

| Check | Result |
| --- | --- |
| Pre-load state | `UD-IQ3_XXS`, Q4, IQ3_M, and IQ4_XS services inactive; `ollama ps` empty |
| Pre-load RAM | About 57 GiB available |
| Pre-load swap | About 2.0 GiB used |
| Pre-load VRAM | About 0.42 GB allocated |
| Health | Did not reach health |
| Guard result | Stopped before health when available RAM dropped below the 8 GiB floor |
| Minimum available RAM observed | About 5541 MiB |
| Maximum swap observed during load | About 4696 MiB |

## Decision

The 64 GiB VRAM / 62 GiB Linux RAM BIOS split improves host headroom, but it
does not make OrcaRouter `IQ3_M` at 64k acceptable under an 8 GiB available-RAM
floor. The load was stopped before health to avoid repeating the earlier
system-stability problems.

The working Hermes hands-on test default was restored to
`qwen3.8-flash-next-unsloth-ud-iq3_xxs` at 16k context on
`llama-qwen38-flashnext-unsloth-ud-iq3xxs.service` / port `11455`, and LiteLLM
smoke returned `pong`.
