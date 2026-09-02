# Qwen3.8-Flash-Next Runtime Attempt

Date: 2026-09-02 (America/Chicago)

## Objective

Prepare a side-by-side Strix Halo ROCm runtime for Qwen3.8-Flash-Next, select
the highest-quality candidate with a defensible fit on the 96 GiB GPU
allocation, and benchmark it only if it loaded cleanly without another model
resident.

This supersedes the earlier same-day preflight. The earlier preflight was
correct that the active ROCm 7.14 llama.cpp build could not support
`qwen4exp`, but upstream changed after that check: the Strix Halo toolbox repo
now publishes a dedicated Qwen3.8-Flash-Next ROCm 10.0 image.

## Runtime Prepared

The workstation backend repo at
`/mnt/ai/llama/amd-strix-halo-toolboxes` was clean and fast-forwarded from
`eb3395a4d138fc490b38405b8f24b3096bce3745` to
`77599c6166318ecf6bcef1df518cbbe60dd63186`.

| Item | Value |
| --- | --- |
| Toolbox repo | `kyuz0/amd-strix-halo-toolboxes` |
| Repo commit | `77599c6166318ecf6bcef1df518cbbe60dd63186` |
| Image | `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-10.0-qwen-3.8-flash-next` |
| Image digest | `docker.io/kyuz0/amd-strix-halo-toolboxes@sha256:d2067225019f61d39c6531322fff8469d67a9a4457c83ed50945b8dffdd818be` |
| Image ID | `2a0d32e0017a80ddd9ec27e17147c94d55c4cb944d8bdbe48ea37696ec7db203` |
| Toolbox | `llama-rocm-10.0-qwen38-flash-next` |
| llama.cpp | `0.3.0-dev`, build `10672`, commit `590ac45bc` |

`llama-cli --list-devices` in the new toolbox detected `ROCm0: AMD Radeon
8060S Graphics (98304 MiB)`.

## Candidate Selection

The selected candidate was
`AtomicChat/Qwen3.8-Flash-Next-GGUF`,
revision `142262902a46f7daed19c79d0771534c8106ad59`, group
`Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64`.

Reasoning:

1. Official BF16 and FP8 checkpoints still do not fit the host.
2. The AtomicChat split GGUF keeps the n-gram table in its own SSD-backed
   shard instead of requiring the full file set to be resident.
3. The publisher reports `AD-4.27bpw-Q4_K_M-M64` at 54.5 GB in memory,
   38.4 GB on SSD, and 92.9 GB total. It is also the publisher's recommended
   build because it matches the 5.00bpw result within measurement error while
   leaving more context headroom.
4. This is a higher-quality first test than the earlier Q2/Q3 fallback path,
   while still excluding vision and MTP.

Downloaded files:

| Item | Value |
| --- | --- |
| Local path | `/mnt/ai/models/qwen38-flash-next-ad-4.27bpw-q4km-m64` |
| File count | 33 GGUF shards |
| Total size | 94,525,394,976 bytes |
| Manifest | `/mnt/ai/models/qwen38-flash-next-ad-4.27bpw-q4km-m64/MANIFEST.sha256` |

All 33 shards passed SHA-256 verification. The first shard parsed successfully
with the new toolbox and exposed `qwen4exp.*`, PLE, and split metadata keys.

## Configuration Changes

Backups:

- `/home/helios/.hermes/backups/qwen38-flash-next-20260902T223653Z`
- `/home/helios/.hermes/backups/qwen38-flash-next-cleanup-20260902T224424Z`

The three qwen3-coder LiteLLM aliases were changed from `keep_alive: 30m` to
`keep_alive: 0`. This was verified with a request to
`hermes-qwen3-coder:30b-128k`; it returned `UNLOAD_OK`, and `ollama ps` was
empty 10 seconds later.

A temporary non-default LiteLLM route and user service were created for
`qwen3.8-flash-next-ad-q4_k_m_m64`, then removed after the load failure so the
Hermes picker does not advertise a broken model. The downloaded model files and
new toolbox remain for evidence or a future owner-directed retest.

## Load Attempt

Before loading Flash:

- Q6 health returned `{"status":"ok"}`.
- `llama-qwen38-uncensored-q6k.service` was stopped.
- `ollama ps` was empty.
- `rocm-smi --showpids` reported no KFD PIDs.
- VRAM used was 746,475,520 bytes.

Temporary service flags:

```text
--host 127.0.0.1 --port 11447
--alias qwen3.8-flash-next-ad-q4_k_m_m64
-m /mnt/ai/models/qwen38-flash-next-ad-4.27bpw-q4km-m64/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-00001-of-00033.gguf
-ngl 99 -c 131072 -b 2048 -ub 2048 -fa on
-ctk f16 -ctv f16 --parallel 1 --jinja -lm dio
--temp 0 --repeat-penalty 1.15
```

The service never reached health. It was repeatedly killed with status `137`
about 30-34 seconds after starting model load. A bounded live check during one
attempt saw the Flash `llama-server` process using 55,683,317,760 bytes of
VRAM, close to the publisher's in-memory claim.

Kernel logs confirmed host RAM OOM, for example:

```text
Out of memory: Killed process 460484 (llama-server)
total-vm:135840216kB anon-rss:22931896kB
```

This is a host memory fit failure, not a normal benchmark result. Direct smoke,
LiteLLM smoke, Hermes tool-call behavior, and the Python telemetry suite were
not run because the model never became healthy.

## Final State

Flash was stopped and removed from active routing. Q6_K was restored as the
only resident/default model.

| Check | Result |
| --- | --- |
| `llama-qwen38-uncensored-q6k.service` | active |
| Q6 health | `{"status":"ok"}` |
| `llama-qwen38-flash-next-ad-q4km-m64.service` | inactive/removed |
| Ollama residents | none |
| Final VRAM used | 27,447,091,200 bytes |
| LiteLLM model list | existing aliases only; no Flash route |

The qwen3-coder `keep_alive: 0` change remains in place and was verified. All
existing Hermes profiles and active LiteLLM model routes were preserved. The
dashboard picker API was not checked because unauthenticated requests returned
401, and the session token was not printed or used.

## Decision

Do not promote Qwen3.8-Flash-Next on the current helios memory split.

The selected Q4_M64 candidate was the best available practical candidate and
the new runtime can parse the architecture metadata, but the host cannot load
it reliably with only about 31 GiB Linux-visible RAM and 8 GiB zram swap. Trying
lower-quality variants after repeated global OOM events would create host
stability risk without producing comparable Q6 replacement evidence.

Revisit only after an owner-approved memory-layout change that increases
Linux-visible RAM/swap headroom, or after a smaller/higher-confidence upstream
candidate exists. Any retest should start non-default, text-only, no MTP, no
vision, and should again unload Q6 and all Ollama runners before loading Flash.
