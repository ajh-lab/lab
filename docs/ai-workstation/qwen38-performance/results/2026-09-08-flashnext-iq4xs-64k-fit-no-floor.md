# Qwen3.8 Flash-Next OrcaRouter IQ4_XS 64k Fit No-Floor Test

Date: 2026-09-08 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Retest the OrcaRouter `IQ4_XS` Flash-Next quant at 64k context on the observed
64 GiB VRAM / 62 GiB Linux RAM BIOS split with no available-RAM floor
requirement.

## Runtime

| Field | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf` |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Port | `11454` |
| Runtime | `llama-server` inside `llama-rocm-10.0-qwen38-flash-next` toolbox |
| Context | `65536` |
| Main flags | `-c 65536 -b 512 -ub 128 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --fit on --fit-target 1536 --no-warmup --no-webui` |
| RAM floor | None |

## Load Result

The first no-floor attempt kept the previous full-offload style with
`-ngl 999`. It failed before health because the 64 GiB VRAM pool filled and
llama.cpp could not allocate another 816 MiB ROCm buffer for the 64k KV cache.

The second attempt removed explicit `-ngl` and used `--fit on --fit-target
1536`.

| Check | Result |
| --- | --- |
| Pre-load state | IQ3_M, `UD-IQ3_XXS`, Q4, and IQ4_XS services inactive; no `llama-server`; `ollama ps` empty |
| Pre-load RAM | `58305` MiB available |
| Pre-load swap | `2861` MiB used |
| Pre-load VRAM | `213618688` bytes allocated |
| Health | Passed after 119 seconds |
| Minimum available RAM observed during load | `8054` MiB |
| Maximum swap observed during load | `28299` MiB |
| Post-load RAM | About `32487` MiB available |
| Post-load swap | About `9572` MiB used |
| Post-load VRAM | `66980159488` bytes allocated |
| Direct smoke | `pong`, about 23.58 tok/s on the tiny response |

## Benchmark Results

Standard LiteLLM benchmark:

| Scenario | Output tokens | Elapsed | Output tok/s |
| --- | ---: | ---: | ---: |
| `smoke` | 4 | 1.03 s | 3.89 |
| `rust-light` | 95 | 3.92 s | 24.22 |
| `code-review` | 117 | 4.93 s | 23.73 |

Controlled Python telemetry benchmark:

| Pass | Hidden tests | Standards probes | Combined | Completion tok/s |
| --- | ---: | ---: | ---: | ---: |
| First | 12/13 | 0/5 | 12/18 | 25.66 |
| Repaired | 12/13 | 1/5 | 13/18 | 22.73 |

After the controlled benchmark, the host still had about `30618` MiB available
RAM, about `9386` MiB swap used, and `67059216384` bytes of ROCm VRAM
allocated.

## Decision

`IQ4_XS` can run at 64k on the 64 GiB VRAM / 62 GiB Linux RAM split only when
llama.cpp is allowed to fit/spill instead of forcing full offload. This avoided
the full-offload ROCm KV-cache OOM, but it used about 28 GiB swap during load
and this run scored much worse than the earlier 96 GiB-VRAM clean IQ4_XS result.

Hermes default and the legacy Discord profile were pointed at
`qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` with 64k context after the
successful fit-mode load. Config backups were written under
`/home/helios/.hermes/backups/promote-iq4xs-64k-fit-no-floor-20260908-075616`,
and the service backup before fit-mode changes was written under
`/home/helios/.config/systemd/user/backups/iq4xs-64k-fit-no-floor-20260908-074914`.

Artifacts:

`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-08-flashnext-iq4xs-64k-fit-no-floor/`
