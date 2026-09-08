# Qwen3.8 Flash-Next OrcaRouter IQ4_XS 96GB Original-Flags Retest

Tested: 2026-09-08 08:22-08:30 America/Chicago.

## Purpose

After the workstation was switched back from the observed 64 GiB VRAM / 62 GiB
Linux RAM BIOS split to the observed 96 GiB VRAM / 31 GiB Linux RAM split, this
run reloaded the OrcaRouter `IQ4_XS` Flash-Next quant with the same full-offload
flags used by the original successful 2026-09-07 benchmark. This retest checks
whether the earlier degraded 64 GiB `--fit` result was caused by the altered
runtime configuration.

## Configuration

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Model source | `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF`, `IQ4_XS` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf` |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Port | `11454` |
| Context | `65536` |
| Main flags | `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |
| MTP | Disabled |
| Toolbox | `llama-rocm-10.0-qwen38-flash-next` |
| BIOS memory split | Observed 96 GiB VRAM / 31 GiB Linux RAM |
| Autostart | Disabled after load; service left active for manual Hermes testing |

## Load And Residency

| Measurement | Value |
| --- | ---: |
| Pre-load available RAM | 26106 MiB |
| Pre-load swap used | 2776 MiB |
| Pre-load VRAM used | 743464960 bytes |
| Pre-load model state | No exact `llama-server`; `ollama ps` empty |
| Health time | 193 seconds |
| Minimum available RAM during load | 518 MiB |
| Maximum swap used during load | 39897 MiB |
| Post-load available RAM | About 11669 MiB |
| Post-load swap used | About 20797 MiB |
| Post-load VRAM used | 70864687104 bytes |
| Post-load model state | Exactly one `llama-server`, IQ4_XS on port `11454`; `ollama ps` empty |

This profile is steady enough for supervised manual testing after it reaches
health, but startup still drives host RAM to an unsafe margin. Keep autostart
disabled.

## Standard LiteLLM Benchmark

| Scenario | Prompt tokens | Completion tokens | Elapsed | Output tok/s |
| --- | ---: | ---: | ---: | ---: |
| `smoke` | 37 | 4 | 0.86 s | 4.64 |
| `rust-light` | 63 | 95 | 3.83 s | 24.78 |
| `code-review` | 86 | 117 | 4.81 s | 24.34 |

## Controlled Python Telemetry Benchmark

| Pass | Hidden tests | Standards probes | Combined | Output tok/s |
| --- | ---: | ---: | ---: | ---: |
| First | 13/13 | 0/5 | 13/18 | 26.18 |
| Repaired | 13/13 | 4/5 | 17/18 | 25.24 |

The repaired candidate only failed the lowercase RFC3339 `t`/`z` standards
probe, matching the earlier clean IQ4_XS result and the 27B OrcaRouter Q4_K_M
remaining defect.

## Interpretation

The original IQ4_XS quality result reproduced when the workstation was back on
the 96 GiB VRAM split and the service used the original `-b 1024 -ub 256`
full-offload flags. The degraded 64 GiB fit/no-floor result should be treated as
a different runtime configuration, not as representative of the model's best
observed quality.

IQ4_XS remains the best hands-on speed/quality candidate when supervised, but it
is not safe as an unattended boot-time default on this memory split because load
time reached only 518 MiB available RAM and used about 39 GiB of swap.

Artifacts:
`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-08-flashnext-iq4xs-96gb-original-flags-64k/`.
