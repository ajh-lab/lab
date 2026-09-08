# BF16 Implementation Evaluation: Python Telemetry Reducer

Date: 2026-09-01 (America/Chicago)

## Objective

Run the exact Q4 Python telemetry-reducer evaluation against the matching
Qwen3.8 27B Uncensored BF16 weights. The model received the same original
prompt, temperature, token limit, hidden tests, standards probes, and two-item
repair feedback. It had no access to the tests and could not deploy or modify a
project repository.

All test and output artifacts are retained under
`results/artifacts/2026-09-01-python-telemetry/`.

## Runtime

| Item | BF16 value |
| --- | --- |
| Service | `llama-qwen38-uncensored-bf16.service` |
| Endpoint | `http://127.0.0.1:11439/v1` |
| LiteLLM model | `qwen3.8-27b-uncensored-bf16` |
| Context | 131072 |
| Batch/microbatch | 1024/256 |
| Approximate loaded GPU memory | 57.6 GB decimal |
| Temperature | 0 |
| Maximum completion tokens | 4096 |

Only BF16 was loaded during generation. After evaluation, BF16 was stopped and
the accepted Q4 service was restored healthy on port `11440` with approximately
22.1 GB decimal GPU memory in use.

## First Attempt

| Metric | Q4 | BF16 |
| --- | ---: | ---: |
| Prompt tokens | 702 | 702 |
| Completion tokens | 2,514 | 2,446 |
| Elapsed time | 212.608 s | 578.806 s |
| Generated module size | 237 lines | 260 lines |
| Core hidden tests | 13/13 | 10/13 |
| Standards tests | 0/5 | 0/5 |
| Combined score | 13/18 | 10/18 |

BF16 failed three core behaviors that Q4 passed: exact gap segmentation, a
`none` fix closing a segment, and equal timestamps starting a new segment. It
also failed all five additional mapping and RFC3339 probes.

## Feedback Cycle

For direct comparability, BF16 received exactly the same two concrete failure
messages that Q4 received:

1. Accept arbitrary `collections.abc.Mapping` implementations.
2. Reject RFC3339 timezone offsets containing seconds.

The model was not shown its other hidden failures.

| Metric | Q4 | BF16 |
| --- | ---: | ---: |
| Prompt tokens | 3,329 | 3,261 |
| Completion tokens | 3,410 | 2,517 |
| Elapsed time | 296.842 s | 605.428 s |
| Generated module size | 317 lines | 268 lines |
| Core hidden tests | 13/13 | 12/13 |
| Standards tests | 3/5 | 2/5 |
| Combined score | 16/18 | 14/18 |

BF16 fixed both reported failures and two of its three unreported core failures.
It retained a bug that rejected valid `none` fix events. It also continued to
accept timestamps without required seconds and compact timezone offsets, and
continued to reject lowercase RFC3339 `t`/`z`.

## Decision

Do not promote BF16. On this task, higher weight precision was both slower and
less correct. One sample cannot establish a universal quality ranking, but it
does reject the hypothesis that BF16 should replace Q4 merely because it
preserves more numerical precision.

Keep Q4 as the local implementation candidate with tests and stronger review.
Use BF16 only for additional controlled evaluations or when a task-specific
benchmark demonstrates a repeatable advantage.

## Intermediate Quantization Candidates

The matching model repository currently offers:

| Quantization | File size | Approximate memory-bound decode estimate |
| --- | ---: | ---: |
| Q4_K_M | 15.66 GiB | 11.6 tok/s measured |
| Q5_K_M | 18.19 GiB | about 10.0 tok/s estimated |
| Q6_K | 20.89 GiB | about 8.7 tok/s estimated |
| Q8_0 | 27.05 GiB | about 6.7 tok/s estimated |
| BF16 | about 51 GiB | 4.1 tok/s measured |

The intermediate throughput figures are rough inverse-size estimates, not
benchmarks. Actual Strix Halo performance must be measured.

Test `Q6_K` next. It provides a meaningful precision increase over Q4_K_M while
remaining far smaller and likely faster than BF16. If Q6 does not improve blind
correctness, retain Q4. Q5 is a reasonable speed-oriented fallback; Q8 is less
attractive unless Q6 demonstrates a quality trend that justifies moving higher.
