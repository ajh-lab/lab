# Qwen3.8 Flash-Next OrcaRouter IQ3_M 131k Manual Test

Date: 2026-09-07 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Check whether the smaller Flash-Next OrcaRouter `IQ3_M` quant can run at
`131072` context and whether it is safe to treat as an always-on setup on the
current 32 GiB system RAM / 96 GiB VRAM BIOS split.

## Runtime

| Field | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` |
| Model path | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq3m/Qwen3.8-Flash-Next-Uncensored-IQ3_M-00001-of-00002.gguf` |
| Runtime | `llama-server` inside `llama-rocm-10.0-qwen38-flash-next` toolbox |
| Test port | `11458` transient test, then `11453` during service promotion attempt |
| Context | `131072` |
| Main flags | `-ngl 999 -c 131072 -b 512 -ub 128 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |

## Observations

| Check | Result |
| --- | --- |
| Transient manual load | Reached health after about 2 minutes 48 seconds |
| Direct smoke | Passed with a `pong` response |
| LiteLLM smoke | Passed while the route was active |
| Reported metadata | `n_ctx=131072`, `n_params=176943899520`, `ftype=IQ3_S mix - 3.66 bpw`, model size about 89.5 GB |
| Settled resource use after transient load | About 19 GiB host RAM used, 11 GiB available, 20 GiB swap used, and about 64.3 GB VRAM used |
| Kernel health after transient load | No immediate AMDGPU/OOM warnings seen |
| Persistent service attempt | Not accepted. The service transition later drove VRAM pressure near the device limit and produced AMDGPU command-submission/OOM evidence. |

## Guarded RAM-Floor Retry

After the Q4 default was restored, a later guarded retry checked whether IQ3_M
could load while preserving at least 12 GiB of available system RAM on the same
32 GiB system RAM / 96 GiB VRAM BIOS split.

Q4 was stopped, `ollama ps` was empty, and ROCm showed effectively no model VRAM
allocation before the retry. The IQ3_M service was then started under a guard
that stopped the service if `free` reported less than 12288 MiB available RAM.

| Attempt | Runtime flags changed | Result |
| --- | --- | --- |
| 131k | Existing restored unit: `-c 131072 -b 512 -ub 128` | Stopped before health after available RAM dropped to about 2519 MiB. |
| 64k | Temporary unit: `-c 65536 -b 512 -ub 128` | Stopped before health after available RAM dropped to about 1366 MiB. |
| 16k | Temporary unit: `-c 16384 -b 256 -ub 64` | Stopped before health after available RAM dropped to about 1743 MiB. |

The IQ3_M unit was restored to the original 131k definition after the test and
left inactive/disabled. The stable Q4 default was restarted and passed a
LiteLLM smoke response.

## Decision

Do not make `IQ3_M` a boot-persistent or always-on user service on the current
32 GiB RAM / 96 GiB VRAM split. It can be used as an explicit manual experiment
when the operator intentionally unloads other large models first and monitors
RAM, swap, VRAM, and kernel logs during load.

The stable Hermes default was restored to
`qwen3.8-27b-uncensored-orcarouter-q4_k_m` at `131072` context through
`llama-qwen38-orcarouter-uncensored-q4km.service` on port `11448`.

## Current State After Rollback

Verified at 2026-09-07T22:20:51-05:00:

| Item | State |
| --- | --- |
| `llama-qwen38-orcarouter-uncensored-q4km.service` | active/enabled |
| `llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service` | inactive/disabled |
| `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` | inactive/disabled |
| Hermes default | `qwen3.8-27b-uncensored-orcarouter-q4_k_m` |
| Hermes context | `131072` |
| Q4 direct health | `{"status":"ok"}` |
| Q4 LiteLLM smoke | `pong` |
| Hermes gateway/dashboard | active/enabled |
| LiteLLM internal/LAN/metrics services | active/enabled |

At verification time, ROCm showed the Q4 llama.cpp process using about 21.4 GB
VRAM and an Ollama `hermes-qwen3-coder:30b-64k` process temporarily holding
about 39.0 GB VRAM. The extra VRAM was Ollama residency, not an IQ3_M process.
