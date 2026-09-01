# E001-E002 Results: Baseline And No-Mmap

Date: 2026-09-01 (America/Chicago)

## E001: Precision Comparison

The Q4_K_M and BF16 files are matching uncensored model variants at different
weight precision. Each model was loaded and tested separately through LiteLLM.

| Scenario | Q4_K_M | BF16 |
| --- | ---: | ---: |
| Rust generation, repeat 1 | 11.91 tok/s | 4.16 tok/s |
| Rust generation, repeat 2 | 11.88 tok/s | 4.16 tok/s |
| Code review, repeat 1 | 11.48 tok/s | 4.08 tok/s |
| Code review, repeat 2 | 11.65 tok/s | 4.21 tok/s |
| 10,298-token context elapsed | 32.80 s | 43.77 s |
| Basic response correctness | Pass | Pass |
| Approximate loaded GPU memory | 22.3 GB | 57.7 GB |

Decision: prefer Q4_K_M for the first restricted worker trial. It generated
approximately 2.8 times faster and used about 35 GB less GPU memory without a
quality difference in this limited test set.

The full `qwen38bf16tools` Hermes smoke test passed with `BF16_PROFILE_OK`.
Hermes supplied an approximately 17.5k-token tool-enabled prompt, which took
about 77 seconds to process before the short response. This demonstrates that
agent prompt overhead is operationally significant even when the model fits.

## E002: Add `--no-mmap`

The exact E001 tests were repeated after adding `--no-mmap` to both services.

| Scenario | Q4 before | Q4 no-mmap | BF16 before | BF16 no-mmap |
| --- | ---: | ---: | ---: | ---: |
| Rust repeat 1 | 11.91 | 11.83 | 4.16 | 4.15 |
| Rust repeat 2 | 11.88 | 11.26 | 4.16 | 4.16 |
| Code review repeat 1 | 11.48 | 11.21 | 4.08 | 4.06 |
| Code review repeat 2 | 11.65 | 11.59 | 4.21 | 4.20 |
| 10,298-token context elapsed | 32.80 s | 33.23 s | 43.77 s | 43.77 s |

Decision: `--no-mmap` did not improve throughput. Retain it because the current
Strix Halo toolbox guidance recommends it for stability and avoidance of mmap
slowdowns. The observed differences are small enough to treat as run variance.

## State After E002

- `llama-qwen38-uncensored-q4km.service`: active and healthy
- `llama-qwen38-uncensored-bf16.service`: configured and stopped
- both units contain `--no-mmap`
- Q4 idle GPU memory: approximately 22.2 GB decimal
- observed post-test GPU state: about 3% busy and 48 C
- Hermes profile configuration unchanged

