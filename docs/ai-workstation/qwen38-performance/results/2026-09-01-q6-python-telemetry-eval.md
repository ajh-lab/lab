# Q6_K Implementation Evaluation: Python Telemetry Reducer

Date: 2026-09-01 (America/Chicago)

## Objective

Evaluate the matching Qwen3.8 27B Uncensored Q6_K release against the exact
blind Python telemetry task and feedback cycle previously used for Q4_K_M,
BF16, and Qwen3-Coder. This isolates weight quantization: prompt, tests,
temperature, context, llama.cpp backend, and server flags were unchanged.

The model had no access to the hidden tests and could not deploy or modify a
repository.

## Model And Runtime

| Item | Value |
| --- | --- |
| Model file | `Qwen3.8-27B-Uncensored-Q6_K.gguf` |
| Source repository | `JonathanColetti/Qwen3.8-27B-Uncensored-GGUF` |
| File size | 22,430,999,968 bytes |
| SHA-256 | `a50aa1478295b58ee3d93eabe02c17f6d5fcf6cb787fd8a0ab07ac629a46cae6` |
| Service | `llama-qwen38-uncensored-q6k.service` |
| Endpoint | `http://127.0.0.1:11446/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-q6_k` |
| Loaded VRAM | 27,386,691,584 bytes |

The runtime used the same `llama-rocm-7.14-q4` toolbox and flags as Q4:

```text
--no-mmap -ngl 99 -c 131072 -b 1024 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off
--temp 0 --repeat-penalty 1.15
```

## First Attempt

| Metric | Result |
| --- | ---: |
| Prompt tokens | 702 |
| Completion tokens | 2,667 |
| Elapsed time | 288.895 s |
| Generated module size | 279 lines |
| Core hidden tests | 13/13 |
| Additional standards tests | 1/5 |
| Combined score | 14/18 |

The first attempt passed every core test and correctly accepted lowercase
RFC3339 `t` and `z`. It still required a concrete `dict`, accepted a timezone
offset containing seconds, accepted timestamps without seconds, and accepted
compact timezone offsets.

## Feedback Cycle

The model received the same two concrete failures used in every comparison:
accept arbitrary mappings and reject timezone offsets containing seconds. The
other three standards probes remained undisclosed.

| Metric | Result |
| --- | ---: |
| Prompt tokens | 3,482 |
| Completion tokens | 2,497 |
| Elapsed time | 281.042 s |
| Generated module size | 271 lines |
| Original hidden tests | 13/13 |
| Standards tests | 3/5 |
| Combined score | 16/18 |

The repair fixed both reported failures, retained lowercase handling, and kept
all core behavior. Like Q4, it did not generalize to the undisclosed missing-
seconds and compact-offset cases.

## Comparison And Decision

| Model | First score | Repaired score | Total elapsed | Repaired lines |
| --- | ---: | ---: | ---: | ---: |
| Q4_K_M | 13/18 | 16/18 | 509.450 s | 317 |
| Q6_K | 14/18 | 16/18 | 569.937 s | 271 |

Q6 took 11.9% longer across both generations and used about 5.2 GB more VRAM
than Q4. It improved blind first-pass correctness by one test, matched Q4 after
feedback, and produced a materially shorter repaired implementation.

Promote Q6_K as the quality-first default local Qwen3.8 worker. Keep Q4_K_M as
the installed rollback and faster option. This is one deterministic task, not
proof of a broad quality advantage; focused tests, CI, and stronger-model review
remain mandatory, and the routing decision should be revisited after several
real GitHub issues.

Final workstation state:

- Q6 service enabled, active, healthy, and loaded
- Q4 service disabled and inactive
- Hermes root default set to `qwen3.8-27b-uncensored-q6_k`
- all existing LiteLLM and Hermes picker entries preserved
- rollback snapshots stored under
  `/home/helios/.hermes/backups/qwen38-q6-20260902T012312Z` and
  `/home/helios/.hermes/backups/qwen38-q6-promotion-20260902T014433Z`
