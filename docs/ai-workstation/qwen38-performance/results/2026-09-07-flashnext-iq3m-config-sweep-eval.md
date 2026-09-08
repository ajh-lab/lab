# Flash-Next OrcaRouter IQ3_M Configuration Sweep

Tested: 2026-09-07 15:40-16:30 America/Chicago

This sweep tested runtime knobs on the current Flash-Next IQ3_M route before
switching to another quant. Each variant restarted the same
`llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service`, waited for
`/health`, ran the standard short LiteLLM benchmark, ran the controlled Python
telemetry benchmark, then ran the same one-pass repair cycle.

The service was restored after the sweep to the previous known-good live flags:

```text
--reasoning off --repeat-penalty 1.0
```

## Environment

| Item | Value |
| --- | --- |
| Host | `ai-workstation-evox2` / `helios@192.168.1.123` |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` |
| Model files | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq3m` |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service` |
| Port | `11453` |
| Context | `65536` |
| MTP | Disabled |
| Runtime | Flash-Next ROCm toolbox `llama-rocm-10.0-qwen38-flash-next` |
| Host memory split | About 96 GB exposed as VRAM and about 30 GiB visible to Linux |
| Swap | `/mnt/ai/swap/qwen-flashnext-test.swap`, 64 GiB, persisted in `/etc/fstab` |
| LiteLLM | `1.97.0`, loopback route `http://127.0.0.1:4004/v1` |
| llama.cpp | `0.3.0-dev`, build `10672`, commit `590ac45bc` |
| OS / kernel | Fedora 43, kernel `7.1.9-100.fc43.x86_64` |
| ROCm | `rocm-smi` reports `3.1.0+unknown` |
| Service backup | `/home/helios/.config/systemd/user/llama-qwen38-flashnext-orcarouter-uncensored-iq3m.service.bak-config-sweep-20260907` |

## Controlled Benchmark Results

| Variant | Key flags | First score | Repaired score | First speed | Repair speed | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Baseline live config | `-b 1024 -ub 256 --reasoning off --repeat-penalty 1.0` | 13/18 | 15/18 | 27.58 tok/s | 25.24 tok/s | Current known-good live runtime before this sweep. |
| Ngram speculative | `-t 16 -tb 32 --spec-type ngram-mod --spec-ngram-mod-n-match 24 --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64` | 13/18 | 15/18 | 27.61 tok/s | 54.51 tok/s | Best speed signal, but mainly on the long repair prompt. Worth manual/long-chat testing before promotion. |
| Threads 8/12 | `-t 8 -tb 12` | 13/18 | 15/18 | 27.79 tok/s | 25.26 tok/s | No material improvement. |
| Threads 12/24 | `-t 12 -tb 24` | 13/18 | 15/18 | 27.88 tok/s | 25.26 tok/s | No material improvement. |
| Threads 16/32 | `-t 16 -tb 32` | 13/18 | 15/18 | 27.92 tok/s | 25.32 tok/s | Slightly best plain-thread setting, but too small to matter. |
| Batch 2048/512 | `-b 2048 -ub 512 -t 16 -tb 32` | 13/18 | 14/18 | 27.98 tok/s | 25.58 tok/s | Reject for now; small speed gain with repaired-score regression. |
| Batch 4096/1024 | `-b 4096 -ub 1024 -t 16 -tb 32` | 13/18 | 14/18 | 28.24 tok/s | 26.25 tok/s | Fastest non-speculative run, but repaired-score regression makes it a poor default. |
| Cache/checkpoint | `-t 16 -tb 32 --cache-ram 32768 --kv-unified --ctx-checkpoints 64` | 13/18 | 15/18 | 27.62 tok/s | 25.17 tok/s | No benefit on this benchmark. May still matter for different long-context patterns. |
| Fit placement | `--fit on --fit-target 1536 -t 8 -tb 12` | 13/18 | 15/18 | 27.53 tok/s | 25.24 tok/s | No benefit versus manual `-ngl 999` placement. |

## Short Benchmark Notes

The ngram speculative variant did not improve short, non-repetitive prompts:

| Scenario | Ngram speculative | Explicit 16/32 threads |
| --- | ---: | ---: |
| Smoke | 3.22 tok/s | 3.45 tok/s |
| Rust light | 25.52 tok/s | 25.56 tok/s |
| Code review | 22.69 tok/s | 25.07 tok/s |

The large repair-prompt win is likely because speculative ngram decoding
benefits from repeated code and prompt structure. It is promising for iterative
coding and long repair prompts, but not a guaranteed general chat speedup.

## Artifacts

Local artifact root:

```text
docs/ai-workstation/qwen38-performance/results/artifacts/flashnext-iq3m-config-sweep-20260907/
```

The copied artifacts include:

- `sweep-summary.json`
- one folder per variant with `summary.json`
- generated candidate and repaired Python modules
- hidden/adversarial test outputs
- standard benchmark outputs
- per-variant system snapshots

## Recommendation

Do not promote the larger batch sizes because they reduced repaired benchmark
quality. The only runtime candidate worth additional manual testing is
`ngram-mod`, because it preserved the controlled score and produced a much
faster long repair generation. Keep the previous known-good service flags live
until that behavior is validated in normal Hermes chat.
