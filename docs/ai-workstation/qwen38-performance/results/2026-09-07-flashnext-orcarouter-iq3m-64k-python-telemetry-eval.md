# Flash-Next OrcaRouter IQ3_M 64k Python Telemetry Evaluation

Tested: 2026-09-07 13:30 America/Chicago

## Runtime Snapshot

| Item | Value |
| --- | --- |
| Host | `fedora` / `ai-workstation-evox2` |
| OS | Fedora Linux 43 Workstation, x86_64 |
| Kernel | `7.1.9-100.fc43.x86_64` |
| GPU | AMD Strix Halo / `gfx1151` |
| Unified memory split | About 96 GB exposed as VRAM, about 30 GiB visible to Linux |
| Swap during test | About 71 GiB total, including `/mnt/ai/swap/qwen-flashnext-test.swap` |
| Hermes | `Hermes Agent v0.21.0 (2026.8.31)` |
| LiteLLM | `1.97.0` |
| llama.cpp | `0.3.0-dev`, build `10672`, commit `590ac45bc` |
| ROCm-SMI | `3.1.0+unknown` |

## Model Route

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` |
| Model source | OrcaRouter Qwen3.8 Flash-Next Uncensored `IQ3_M` split GGUF |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service` |
| llama.cpp endpoint | `http://127.0.0.1:11453/v1` |
| LiteLLM endpoint | `http://127.0.0.1:4004/v1` |
| Context | `65536` |
| MTP | Not enabled for this service; MTP smoke was slower than no-MTP on the short prompt |
| Loaded VRAM | About 63.3 GB decimal during service idle/test |
| Current Hermes role | Experimental manual UI test default; service enabled for login boot |

## Controlled Python Telemetry Benchmark

The same hidden benchmark used for the Q4, Q6, BF16, Qwen3-Coder, and MTP
comparisons was reused:

- 13 hidden behavioral tests
- 5 additional RFC3339/mapping standards probes
- deterministic temperature `0`
- one identical two-failure repair prompt

| Pass | Hidden tests | Standards probes | Combined | Generation time | Completion tokens | Output tok/s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| First | 13/13 | 0/5 | 13/18 | 97.376 s | 2601 | 26.71 |
| Repaired | 13/13 | 2/5 | 15/18 | 115.939 s | 2828 | 24.39 |

## Remaining Defects

First pass failed all five standards probes:

- Rejected read-only `collections.abc.Mapping` implementations such as `MappingProxyType`.
- Accepted RFC3339 timezone offsets containing seconds.
- Accepted timestamps without seconds.
- Accepted compact timezone offsets without a colon.
- Rejected lowercase RFC3339 `t` / `z`.

After repair, the model fixed the mapping issue and the offset-with-seconds
case, but still:

- Accepted timestamps without seconds.
- Accepted compact timezone offsets.
- Rejected lowercase RFC3339 `t` / `z`.

## Short Standard Benchmark

| Scenario | Prompt tokens | Completion tokens | Elapsed | Output tok/s | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Smoke | 37 | 4 | 0.802 s | 4.99 | Returned `BENCH_OK` |
| Rust light | 63 | 104 | 4.448 s | 23.38 | Returned a concise Cargo project layout and source |
| Code review | 86 | 141 | 6.206 s | 22.72 | Identified division-by-zero and returned corrected code |

## Decision

Flash-Next OrcaRouter IQ3_M is a good manual UI speed experiment. It is much
faster than the 27B Q4/Q6 routes on this benchmark, but its repaired score was
15/18, below OrcaRouter Q4_K_M's 17/18 result. Keep it as the active test
default only while evaluating hands-on behavior. The controlled-quality rollback
remains `qwen3.8-27b-uncensored-orcarouter-q4_k_m` at 131k.

Post-test persistence: the Flash-Next user service was enabled and
`/mnt/ai/swap/qwen-flashnext-test.swap` was added to `/etc/fstab` with `nofail`
and `x-systemd.requires-mounts-for=/mnt/ai`, so a reboot should not leave Hermes
pointing at an unstarted default model.

Artifacts:
`docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-python-telemetry/`
