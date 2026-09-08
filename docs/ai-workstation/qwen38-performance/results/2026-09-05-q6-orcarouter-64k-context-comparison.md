# Q6_K And OrcaRouter Q4_K_M 64k Context Comparison

Date: 2026-09-05 (America/Chicago)

## Purpose

Retest the two best non-MTP Qwen3.8 candidates at 64k context to see whether
lowering context changes controlled coding quality, throughput, or VRAM.

The normal Hermes default was preserved as the rollback target:
`qwen3.8-27b-uncensored-q6_k` on port `11446` with 131k context. The 64k tests
used separate test aliases and services.

## Runtime Routes

| Model alias | Service | Port | Context | Final state |
| --- | --- | ---: | ---: | --- |
| `qwen3.8-27b-uncensored-q6_k-64k` | `llama-qwen38-uncensored-q6k-64k.service` | 11451 | 65536 | Test route only |
| `qwen3.8-27b-uncensored-orcarouter-q4_k_m-64k` | `llama-qwen38-orcarouter-uncensored-q4km-64k.service` | 11452 | 65536 | Test route only |

Both routes were registered in LiteLLM at `http://127.0.0.1:4004/v1`. The test
runner serialized model residency: unload current model, load one 64k candidate,
test it, unload it, load the next candidate, test it, then restore the normal
Q6_K 131k default.

## Results

| Model | Context | Loaded VRAM | First score | Repaired score | First generation | Repair generation |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `qwen3.8-27b-uncensored-q6_k-64k` | 65536 | About 24.9 GB total; `llama-server` about 24.1 GB | 14/18 | 16/18 | 2667 tokens in 296.332 s, 9.00 tok/s | 2497 tokens in 283.922 s, 8.79 tok/s |
| `qwen3.8-27b-uncensored-orcarouter-q4_k_m-64k` | 65536 | About 19.7 GB total; `llama-server` about 18.9 GB | 14/18 | 17/18 | 2310 tokens in 199.352 s, 11.59 tok/s | 2343 tokens in 210.858 s, 11.11 tok/s |

## Short Throughput Smoke

| Model | Smoke | Rust-light | Code-review |
| --- | ---: | ---: | ---: |
| Q6_K 64k | 4.20 tok/s | 8.88 tok/s | 8.00 tok/s |
| OrcaRouter Q4_K_M 64k | 5.67 tok/s | 11.88 tok/s | 11.04 tok/s |

## Quality Notes

Q6_K 64k matched the earlier 131k Q6_K score:

- First pass: 13/13 hidden tests and 1/5 standards probes.
- Repair pass: 13/13 hidden tests and 3/5 standards probes.
- Remaining repaired defects: accepted missing-seconds and compact-offset timestamps.

OrcaRouter Q4_K_M 64k matched the earlier 131k OrcaRouter score:

- First pass: 13/13 hidden tests and 1/5 standards probes.
- Repair pass: 13/13 hidden tests and 4/5 standards probes.
- Remaining repaired defect: rejected lowercase RFC3339 `t`/`z`.

## Decision

Reducing these non-MTP routes from 131k to 64k did not reduce quality on the
controlled Python telemetry benchmark. It reduced loaded VRAM by about 2.5 GB
for Q6_K and about 1.7 GB for OrcaRouter Q4_K_M while keeping throughput in the
same practical range.

OrcaRouter Q4_K_M remains the highest-scoring local Qwen3.8 candidate on this
benchmark. After this comparison, the 131k OrcaRouter Q4_K_M route was promoted
to the current Hermes default. Q6_K remains the conservative fallback and the
strongest non-OrcaRouter Q6 baseline.

Artifacts are stored in
`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-05-64k-context-comparison/`.
