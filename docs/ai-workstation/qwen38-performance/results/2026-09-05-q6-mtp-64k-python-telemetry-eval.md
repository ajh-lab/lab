# Qwen3.8 27B Uncensored Q6_K MTP 64k Evaluation

Date: 2026-09-05 (America/Chicago)

## Runtime Setup

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-27b-uncensored-q6_k-mtp` |
| Target GGUF | `/mnt/ai/models/qwen38-uncensored-q6k/Qwen3.8-27B-Uncensored-Q6_K.gguf` |
| Draft GGUF | `/mnt/ai/models/qwen38-uncensored-q4km-mtp-draft/Qwen3.8-27B-Uncensored-draft-Q4_0.gguf` |
| Service | `llama-qwen38-uncensored-q6k-mtp.service` |
| llama.cpp endpoint | `http://127.0.0.1:11450/v1` |
| LiteLLM route | `http://127.0.0.1:4004/v1` -> `http://127.0.0.1:11450/v1` |
| Context | `65536` |
| Batch / microbatch | `1024` / `256` |
| MTP flags | `--spec-draft-model ... --spec-type draft-mtp --spec-draft-n-max 2 --spec-draft-p-min 0` |
| Backup directory | `/home/helios/.hermes/backups/qwen38-q6-mtp-64k-20260905-161554` |

The previous Q4 MTP default was backed up, stopped, and disabled before testing.
The unrelated resident Ollama `hermes-qwen3-coder:30b-256k` process was also
unloaded so the final GPU snapshot only showed the Q6 MTP `llama-server`.

## Health And Routing

| Check | Result |
| --- | --- |
| Direct llama.cpp health | Passed on `127.0.0.1:11450` |
| LiteLLM model discovery | Included `qwen3.8-27b-uncensored-q6_k-mtp` |
| LiteLLM smoke | Returned `Q6_MTP_64K_READY` |
| Hermes gateway/dashboard | Active after restart |
| Q6 MTP service | Active and enabled |
| Prior Q4 MTP service | Inactive and disabled |
| Prior non-MTP Q6/Q4 services | Inactive and disabled |
| Idle VRAM after cleanup | About 26.9 GB total used; `llama-server` process about 26.1 GB |

## Standard Throughput Smoke

| Scenario | Prompt tokens | Completion tokens | Elapsed | Output tok/s | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `smoke` | 37 | 4 | 0.669 s | 5.98 | Passed |
| `rust-light` | 63 | 96 | 4.352 s | 22.06 | Passed |
| `code-review` | 86 | 58 | 3.445 s | 16.84 | Passed |

These are short prompts, so the numbers should be treated as smoke/route health
checks rather than full user-session performance predictions.

## Controlled Python Telemetry Benchmark

The same hidden benchmark used for the prior Q4, Q6, BF16, Qwen3-Coder,
OrcaRouter Q4, and Q4 MTP runs was reused:

- exact `prompt.txt`
- 13 hidden behavioral tests
- 5 adversarial Mapping/RFC3339 probes
- temperature `0`
- `max_tokens=4096`
- one identical two-failure repair prompt

| Pass | Hidden tests | Standards probes | Combined | Generation time | Completion tokens | Output tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| First | 5/13 | 0/5 | 5/18 | 144.161 s | 2950 | 20.46 |
| Repaired | 5/13 | 1/5 | 6/18 | 147.618 s | 2977 | 20.17 |

## Main Defects

The generated module had broad implementation defects that dominated both
passes:

- `NameError: name 'segs' is not defined` in multiple normal track-reconstruction cases.
- `UnboundLocalError` around `dlambda` in distance/sorting/gap cases.
- Rejected read-only `Mapping` input on the first pass.
- Still rejected lowercase RFC3339 `t`/`z` after repair.
- Repair only improved the standards probe score from 0/5 to 1/5 and did not fix the core hidden-test failures.

## Decision

`qwen3.8-27b-uncensored-q6_k-mtp` was useful as a manual Hermes Web UI speed
experiment, but it was not a quality improvement over the non-MTP Q6_K route on
this controlled task. The non-MTP Q6_K result remains the stronger Q6 baseline:
14/18 first pass and 16/18 repaired. A later comparison promoted the
OrcaRouter Q4_K_M 131k route as the current Hermes default.

Artifacts for this run are stored in
`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-05-q6-mtp-64k-python-telemetry/`.
