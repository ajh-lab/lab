# Qwen3.8 Flash-Next OrcaRouter IQ3_M 64k Post-BIOS 4GB Floor Test

Date: 2026-09-08 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Retest the OrcaRouter `IQ3_M` Flash-Next quant at 64k context after changing
the BIOS split to observed 64 GiB VRAM / 62 GiB Linux RAM, this time lowering
the available-RAM floor from 8 GiB to 4 GiB.

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
| RAM floor | `4096` MiB available RAM |

## Load Result

| Check | Result |
| --- | --- |
| Pre-load state | `UD-IQ3_XXS`, Q4, IQ3_M, and IQ4_XS services inactive; no `llama-server`; `ollama ps` empty |
| Pre-load RAM | `59102` MiB available |
| Pre-load swap | `2500` MiB used |
| Pre-load VRAM | `420417536` bytes allocated |
| Health | Passed after 34 seconds |
| Minimum available RAM observed during load | `4535` MiB |
| Maximum swap observed during load | `2501` MiB |
| Post-load RAM | About `30785` MiB available |
| Post-load VRAM | `62614179840` bytes allocated |
| Direct smoke | `pong`, about 27.13 tok/s on the tiny response |

## Benchmark Results

Standard LiteLLM benchmark:

| Scenario | Output tokens | Elapsed | Output tok/s |
| --- | ---: | ---: | ---: |
| `smoke` | 4 | 0.82 s | 4.87 |
| `rust-light` | 105 | 3.98 s | 26.39 |
| `code-review` | 136 | 5.23 s | 25.99 |

Controlled Python telemetry benchmark:

| Pass | Hidden tests | Standards probes | Combined | Completion tok/s |
| --- | ---: | ---: | ---: | ---: |
| First | 12/13 | 0/5 | 12/18 | 27.68 |
| Repaired | 12/13 | 1/5 | 13/18 | 23.67 |

After the controlled benchmark, the host still had about `28630` MiB available
RAM, about `2164` MiB swap used, and `62703439872` bytes of ROCm VRAM
allocated.

## Decision

The model can load on the 64 GiB VRAM / 62 GiB Linux RAM split when the floor is
lowered to 4 GiB. The margin is thin: minimum available RAM during load was only
about 4.4 GiB, so this should still be treated as a monitored manual-test
configuration rather than a conservative always-on service.

Hermes default and the legacy Discord profile were pointed at
`qwen3.8-flash-next-uncensored-orcarouter-iq3_m` with 64k context after the
successful load. Config backups were written under
`/home/helios/.hermes/backups/promote-iq3m-64k-floor4g-20260908-073418`, and
the LiteLLM backup was written under
`/home/helios/.config/litellm/backups/config.promote-iq3m-64k-floor4g-20260908-073418.yaml`.

Artifacts:

`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-08-flashnext-iq3m-64k-post-bios-floor4g/`
