# OrcaRouter Q4_K_M Implementation Evaluation: Python Telemetry Reducer

Date: 2026-09-03 (America/Chicago)

## Objective

Evaluate the Qwen3.8 27B OrcaRouter uncensored Q4_K_M test model against the
same controlled coding benchmark used for Q4_K_M, Q6_K, BF16, and Qwen3-Coder.
This isolates the model family change while keeping the benchmark prompt,
hidden tests, feedback cycle, temperature, context, llama.cpp backend, and
server flags aligned with the existing Qwen3.8 evaluation protocol.

The model had no access to the hidden tests and could not deploy or modify a
repository.

## Model And Runtime

| Item | Value |
| --- | --- |
| Model file | `Qwen3.8-27B-Uncensored-OrcaRouter-Q4_K_M.gguf` |
| Source repository | `chimingw/Qwen3.8-27B-Uncensored-OrcaRouter-GGUF` |
| Source lineage | `orcarouter/Qwen3.8-27B-Uncensored-FP8` |
| Revision | `58ebd123013160600229eda180b5b17f3fb7af9d` |
| File size | 16,810,714,496 bytes |
| SHA-256 | `3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec` |
| Service | `llama-qwen38-orcarouter-uncensored-q4km.service` |
| Endpoint | `http://127.0.0.1:11448/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-orcarouter-q4_k_m` |
| Loaded VRAM | about 21% of GPU memory after the run |

The runtime used the same `llama-rocm-7.14-q4` toolbox and standard
llama.cpp flags used by the Qwen3.8 comparison services:

```text
--no-mmap -ngl 99 -c 131072 -b 1024 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off
--temp 0 --repeat-penalty 1.15
```

Before testing, the Q6_K service was inactive, the OrcaRouter service was
active and healthy, LiteLLM and Hermes were active, and `ollama ps` was empty.

## Standard LiteLLM Benchmark

Raw records:

- `results/raw/qwen38-orcarouter-q4km-standard-20260903.jsonl`
- `results/raw/qwen38-orcarouter-q4km-context-20260903.jsonl`

| Scenario | Repeat | Prompt tokens | Completion tokens | Elapsed | Completion tok/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| smoke | 1 | 37 | 4 | 0.774 s | 5.17 |
| rust-light | 1 | 63 | 96 | 8.077 s | 11.89 |
| code-review | 1 | 86 | 65 | 5.717 s | 11.37 |
| smoke | 2 | 37 | 4 | 0.666 s | 6.01 |
| rust-light | 2 | 63 | 96 | 8.280 s | 11.59 |
| code-review | 2 | 86 | 65 | 5.608 s | 11.59 |
| long-16000 | 1 | 10,298 | 6 | 32.715 s | 0.18 |

All standard benchmark calls succeeded. `ollama ps` was empty before and after
both benchmark commands.

## First Attempt

| Metric | Result |
| --- | ---: |
| Prompt tokens | 702 |
| Completion tokens | 2,310 |
| Elapsed time | 200.543 s |
| Generated module size | 240 lines |
| Core hidden tests | 13/13 |
| Additional standards tests | 1/5 |
| Combined score | 14/18 |

The first attempt passed every core hidden test. The only standards probe it
passed was support for read-only `Mapping` implementations. It accepted several
invalid RFC3339 timestamp forms and rejected lowercase `t`/`z`.

## Feedback Cycle

The model received the same two concrete failures used in prior comparisons:
accept arbitrary mappings and reject timezone offsets containing seconds. The
other three standards probes remained undisclosed.

| Metric | Result |
| --- | ---: |
| Prompt tokens | 3,125 |
| Completion tokens | 2,343 |
| Elapsed time | 204.901 s |
| Generated module size | 245 lines |
| Original hidden tests | 13/13 |
| Standards tests | 4/5 |
| Combined score | 17/18 |

The repair retained all original hidden-test behavior and generalized to the
undisclosed missing-seconds and compact-offset cases. The remaining failure was
lowercase RFC3339 `t`/`z` handling.

## Comparison And Decision

| Model | First score | Repaired score | Total elapsed | Repaired lines |
| --- | ---: | ---: | ---: | ---: |
| Q4_K_M | 13/18 | 16/18 | 509.450 s | 317 |
| Q6_K | 14/18 | 16/18 | 569.937 s | 271 |
| OrcaRouter Q4_K_M | 14/18 | 17/18 | 405.444 s | 245 |
| Qwen3-Coder 30B-A3B Q8_0 | 10/18 | 12/18 | 111.244 s | 237 |

The OrcaRouter Q4_K_M model produced the best score seen so far on this single
deterministic task and did so faster than the existing Q4_K_M and Q6_K
Qwen3.8 comparisons. This is strong enough to keep it available for hands-on
testing, but not enough to replace the Q6_K default worker without real issue
execution, CI evidence, and stronger-model review.

Keep the current runtime as a test route/profile. Q6_K remains the configured
default and rollback model.

Final workstation state:

- OrcaRouter service active, healthy, and loaded
- Q6 service inactive
- LiteLLM and Hermes user services active
- `ollama ps` empty
- `rocm-smi --showpids --showmemuse --csv` reporting 21% GPU memory allocated
