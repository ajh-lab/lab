# E005 Results: Batch And Microbatch Matrix

Date: 2026-09-01 (America/Chicago)

## Variable Under Test

ROCm 10 and the exact Q4_K_M model were held constant while batch and
microbatch changed.

| Candidate | Batch | Microbatch |
| --- | ---: | ---: |
| Control | 1024 | 256 |
| B2048 | 2048 | 512 |
| B4096 | 4096 | 1024 |

## Initial Results

| Scenario | 1024/256 | 2048/512 | 4096/1024 |
| --- | ---: | ---: | ---: |
| Rust repeat 1 | 11.87 | 11.90 | 11.87 |
| Rust repeat 2 | 11.85 | 11.89 | 11.22 |
| Code review repeat 1 | 11.42 | 11.50 | 11.40 |
| Code review repeat 2 | 11.98 | 11.63 | 11.13 |
| 10,298-token context elapsed | 32.73 s | 31.82 s | 32.49 s |

The initial `2048/512` context result appeared about 2.8% faster. Additional
cold-start repetitions were required before accepting it.

## Prompt-Cache Correction

The benchmark harness sends the same long prompt repeatedly. Repeating against
one live llama.cpp slot reuses its prompt cache, producing invalid sub-second
results after the first request. Valid cold comparisons therefore restart the
model service before every run.

| Cold 10,298-token run | 1024/256 | 2048/512 |
| --- | ---: | ---: |
| Run 1 | 32.88 s | 31.86 s |
| Run 2 | 32.83 s | 33.93 s |
| Run 3 | 32.89 s | 32.13 s |
| Mean | 32.87 s | 32.64 s |

The candidate mean was only about 0.7% faster and had greater variance.

## Decision

Retain `1024/256`. Neither larger candidate produced a repeatable material
improvement, and `4096/1024` reduced decode consistency. Record prompt-cache
behavior as part of the standard benchmark protocol.

## Cleanup Observation

Stopping the `2048/512` toolbox-backed systemd test unit left its child
`llama-server` process alive without a listening socket. It continued holding
about 22 GB of VRAM and drove reported GPU use to 100%. The exact orphaned test
PID was terminated; the primary `11440` service remained healthy and was not
restarted. Final verification showed one Qwen listener, one GPU process, about
22.2 GB of VRAM in use, and low idle GPU activity.

For later experiments, successful cleanup requires all four checks:

1. Test unit is inactive.
2. Test port is not listening.
3. No test `llama-server` PID remains.
4. VRAM and GPU activity return to the single-primary baseline.
