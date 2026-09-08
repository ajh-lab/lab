# Qwen3.8 Flash-Next OrcaRouter IQ4_XS Clean-Slate RAM-Floor Retest

Date: 2026-09-07 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Purpose

Retest `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` after removing the
known incidental qwen-coder trigger:

- The live `kalshi-research-bot-worker` CronJob scheduled at `17 * * * *` was
  deleted from k3s.
- ArgoCD self-heal for `kalshi-research-bot` was temporarily disabled so the
  CronJob would not immediately return before the source PR lands.
- LiteLLM qwen-coder aliases were changed from `keep_alive: 30m` to
  `keep_alive: 0s`.
- `ollama ps` was empty, Q4 was stopped, and ROCm showed no model PIDs before
  the IQ4_XS retest.

## 64k Manual Retest

| Field | Value |
| --- | --- |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Boot persistence | disabled |
| Context | `65536` |
| Batch / microbatch | `512 / 128` |
| Health | passed |
| LiteLLM smoke | `pong` |
| VRAM used | about 70.7 GB decimal |
| Steady host RAM | about 19 GiB used, 11 GiB available |
| Swap used | about 20 GiB |
| Kernel GPU errors | no increase during the guarded load |

Decision: 64k can run from a clean slate, but it does not meet the requested
12 GiB available system-RAM floor on the current 32 GiB RAM / 96 GiB VRAM BIOS
split.

## 32k Manual Retest

| Field | Value |
| --- | --- |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Boot persistence | disabled |
| Context | `32768` |
| Batch / microbatch | `512 / 128` |
| Health | failed to reach health before guard stop |
| Stop reason | available RAM dropped to 484 MiB during load |
| Swap used at stop | about 37.6 GiB |
| VRAM during load | about 69.2 GB decimal |
| Kernel GPU errors | no increase before the memory guard stopped the run |

Decision: lowering context from 64k to 32k did not solve the load-time system-RAM
pressure. The main bottleneck appears to be the Flash-Next load path and model
mapping pressure, not just the KV context size.

## Final State

After the test, the stale Flash-Next toolbox/container state was cleared and
Hermes was restored to the working lower-VRAM default:

| Item | State |
| --- | --- |
| Hermes default | `qwen3.8-27b-uncensored-orcarouter-q4_k_m` |
| Hermes context | `131072` |
| Q4 service | `llama-qwen38-orcarouter-uncensored-q4km.service` active/enabled |
| IQ4_XS service | inactive/disabled |
| IQ3_M service | inactive/disabled |
| LiteLLM Q4 smoke | `pong` |
| Ollama resident models | none |
| Final Q4 VRAM | about 22.1 GB decimal |
| Final available host RAM | about 24 GiB |
