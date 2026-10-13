# Qwen3-Coder Implementation Evaluation: Python Telemetry Reducer

Date: 2026-09-01 (America/Chicago)

## Candidate Selection

Use the resident `hermes-qwen3-coder:30b-128k` model. It is an existing Ollama
alias over `qwen3-coder:30b-a3b-q8_0`, is already routed through LiteLLM, and
uses the same 131072-token context target as the Qwen3.8 candidates. No model
download or duplicate runtime configuration was needed.

This was the most appropriate resident Qwen3-Coder candidate because it uses
the higher-precision Q8_0 weights and the worker-sized context. The smaller
resident `qwen3-coder:latest` would reduce memory and potentially improve speed,
but would not be a stronger quality comparison.

## Runtime

| Item | Value |
| --- | --- |
| Base model | `qwen3-coder:30b-a3b-q8_0` |
| Evaluation alias | `hermes-qwen3-coder:30b-128k` |
| Backend | Ollama through internal LiteLLM |
| Context | 131072 |
| Temperature override | 0 |
| Maximum completion tokens | 4096 |
| Loaded GPU allocation | About 45.8 GB decimal |

Qwen3.8 Q4 was stopped during generation. After the evaluation, Qwen3-Coder was
unloaded and Qwen3.8 Q4 was restored healthy as the only model process on port
`11440`, using approximately 22.2 GB decimal GPU memory.

## First Attempt

| Metric | Qwen3-Coder | Qwen3.8 Q4 | Qwen3.8 BF16 |
| --- | ---: | ---: | ---: |
| Prompt tokens | 671 | 702 | 702 |
| Completion tokens | 2,196 | 2,514 | 2,446 |
| Elapsed time | 58.123 s | 212.608 s | 578.806 s |
| Generated module size | 236 lines | 237 lines | 260 lines |
| Core hidden tests | 10/13 | 13/13 | 10/13 |
| Standards tests | 0/5 | 0/5 | 0/5 |
| Combined score | 10/18 | 13/18 | 10/18 |

Qwen3-Coder correctly handled normalization, deduplication, sorting,
segmentation, no-fix events, equal timestamps, antimeridian distance, and input
materialization. It accepted bool where a real number was required for gap or
coordinate validation, calculated maximum speed from the wrong time baseline,
required a concrete `dict`, and failed all initial strict RFC3339 probes.

## Feedback Cycle

For direct comparability, the model received exactly the same two failure
messages as both Qwen3.8 candidates: accept arbitrary mappings and reject
timezone offsets containing seconds. It did not see any other test output.

| Metric | Qwen3-Coder | Qwen3.8 Q4 | Qwen3.8 BF16 |
| --- | ---: | ---: | ---: |
| Prompt tokens | 2,976 | 3,329 | 3,261 |
| Completion tokens | 2,152 | 3,410 | 2,517 |
| Elapsed time | 53.121 s | 296.842 s | 605.428 s |
| Generated module size | 233 lines | 317 lines | 268 lines |
| Core hidden tests | 11/13 | 13/13 | 12/13 |
| Standards tests | 1/5 | 3/5 | 2/5 |
| Combined score | 12/18 | 16/18 | 14/18 |

The repair fixed maximum-speed calculation and rejected timezone offsets with
seconds. It did not fix the explicitly reported arbitrary-mapping requirement,
continued to accept bool in numeric validation, and retained three additional
RFC3339 failures.

## Decision

Qwen3-Coder is the clear throughput winner, completing both generations in
under one minute. It is not the correctness winner on this task and should not
replace Qwen3.8 Q4 as the general DroneOps implementation model.

Use Qwen3-Coder for narrowly scoped, low-risk work with strong tests:

- documentation and issue preparation
- boilerplate and project scaffolding
- mechanical test creation
- focused UI adjustments
- formatting and repetitive refactors

Keep Qwen3.8 Q4 for broader implementation, debugging, and contract-heavy work.
Neither local model should merge authentication, persistence, migration,
protocol, or flight-safety changes without stronger review.
