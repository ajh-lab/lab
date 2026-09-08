# Qwen3.8 Flash-Next Unsloth UD-IQ3_XXS 16k Post-BIOS Test

Date: 2026-09-07 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Test the smaller `UD-IQ3_XXS` Flash-Next quant after changing the BIOS memory
split from the earlier 32 GiB system RAM / 96 GiB VRAM setup to an observed
64 GiB VRAM / 62 GiB Linux RAM setup.

This run used an 8 GiB available-RAM floor during model load.

## Runtime

| Field | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-unsloth-ud-iq3_xxs` |
| Hugging Face repo | `unsloth/Qwen3.8-Flash-Next-GGUF` |
| Quant folder | `UD-IQ3_XXS` |
| Model path | `/mnt/ai/models/qwen38-flashnext-unsloth-ud-iq3xxs/UD-IQ3_XXS/Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf` |
| Service | `llama-qwen38-flashnext-unsloth-ud-iq3xxs.service` |
| Port | `11455` |
| Runtime | `llama-server` inside `llama-rocm-10.0-qwen38-flash-next` toolbox |
| Context | `16384` |
| Main flags | `-ngl 99 -c 16384 -b 512 -ub 128 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |

## Load Result

| Check | Result |
| --- | --- |
| Pre-load RAM | About 56 GiB available |
| Pre-load VRAM | About 0.42 GB allocated |
| Health | Passed on port `11455` |
| Minimum available RAM during load | About 15.8 GiB |
| Settled RAM after benchmark | About 26 GiB available |
| Settled swap after benchmark | About 2.1 GiB used |
| Settled VRAM after benchmark | About 53.9 GB allocated; `llama-server` about 53.4 GB |
| Direct llama.cpp smoke | `pong` |
| LiteLLM smoke | `pong` |

## Standard Benchmark

| Scenario | Result |
| --- | --- |
| smoke | 4 output tokens in 0.91 s, about 4.39 tok/s |
| rust-light | 105 output tokens in 4.79 s, about 21.92 tok/s |
| code-review | 136 output tokens in 6.23 s, about 21.84 tok/s |

## Controlled Telemetry Benchmark

| Pass | Hidden tests | Adversarial tests | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 5/13 | 0/5 | 5/18 | 23.16 tok/s |
| Repaired | 12/13 | 4/5 | 16/18 | 19.91 tok/s |

The first pass had a structural implementation bug around `build_segment` and
also rejected read-only mappings and lowercase RFC3339 `t`/`z`.

The repair pass fixed most behavior. Remaining failures:

- `computes distance speed and best fix`
- `accepts lowercase RFC3339 t and z`

## Decision

`UD-IQ3_XXS` is the first Flash-Next route that satisfies the 8 GiB available
system-RAM floor on the 64 GiB VRAM / 62 GiB Linux RAM split. It is loaded as
the current Hermes hands-on test default at 16k context.

Treat it as an interactive speed/stability candidate, not as the quality
baseline yet. The first-pass score was weak, but the repaired score is close to
the stronger existing baselines. For quality-sensitive coding, the current
rollback remains `qwen3.8-27b-uncensored-orcarouter-q4_k_m`.

## Artifacts

Full raw responses, candidates, tests, and summaries are stored under:

`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-unsloth-ud-iq3xxs-16k-post-bios/`
