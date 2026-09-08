# Flash-Next OrcaRouter IQ4_XS 64k Python Telemetry Evaluation

Tested: 2026-09-07 17:55-18:03 America/Chicago

This run tested the next larger OrcaRouter Flash-Next uncensored quant after
`IQ3_M`. The chosen quant was `IQ4_XS` because the model card describes it as
the best low-bit pick, approximately `Q4_K_S` quality at a smaller size, while
`Q4_K_M` is much larger and riskier under the current memory split.

## Environment

| Item | Value |
| --- | --- |
| Host | `ai-workstation-evox2` / `helios@192.168.1.123` |
| Model source | `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF` |
| Quant | `IQ4_XS`, three GGUF shards |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Model files | `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs` |
| Model size on disk | 91 GiB |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Port | `11454` |
| Context | `65536` |
| MTP | Disabled |
| Runtime flags | `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |
| Runtime | Flash-Next ROCm toolbox `llama-rocm-10.0-qwen38-flash-next` |
| Host memory split | About 96 GB exposed as VRAM and about 30 GiB visible to Linux |
| Loaded VRAM | About 71.1 GB decimal total with IQ4_XS loaded |
| Swap | 64 GiB disk-backed swap file persisted under `/mnt/ai/swap/` |
| LiteLLM | `1.97.0`, loopback route `http://127.0.0.1:4004/v1` |
| llama.cpp | `0.3.0-dev`, build `10672`, commit `590ac45bc` |
| OS / kernel | Fedora 43, kernel `7.1.9-100.fc43.x86_64` |
| Config backup | `/home/helios/.hermes/backups/flashnext-iq4xs-test-20260907-173356` |
| Promotion backup | `/home/helios/.hermes/backups/promote-flashnext-iq4xs-20260907-180340` |

## Load Notes

The first IQ4_XS load attempt failed because the previous IQ3_M
`llama-server` process remained alive after the user service was marked failed,
still holding about 62 GB of VRAM. After force-clearing that stale process,
IQ4_XS loaded cleanly and reached `/health` on port `11454`.

A later Discord-route check found a separate Ollama runner for
`hermes-qwen3-coder:30b-64k` loaded after this benchmark and holding about
39 GB of VRAM. That later two-model state caused IQ4_XS reload failures until
Ollama was unloaded. A clean confirmation run with `ollama ps` empty reproduced
the same 13/18 first and 17/18 repaired score; see
`2026-09-07-flashnext-orcarouter-iq4xs-64k-clean-confirmation.md`.

## Results

| Variant | First score | Repaired score | First speed | Repair speed | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Baseline | 13/18 | 17/18 | 26.92 tok/s | 24.88 tok/s | Promote for manual Hermes testing. This ties the best repaired quality score while staying far faster than 27B Q4/Q6. |
| Clean confirmation | 13/18 | 17/18 | 27.24 tok/s | 25.41 tok/s | Confirms the baseline result with Ollama unloaded and only IQ4_XS resident in VRAM. |
| Strict system prompt | 14/18 | 14/18 | 27.75 tok/s | 25.49 tok/s | Reject for IQ4_XS. The repair pass overcorrected valid RFC3339 timezone offsets and dropped hidden-test quality. |

The baseline repaired result passed all hidden tests and 4/5 standards probes.
The only remaining standards failure after repair was lowercase RFC3339 `t` /
`z`, matching the remaining defect seen with the previous 27B OrcaRouter
`Q4_K_M` quality baseline.

## Short Benchmark

| Scenario | Result |
| --- | ---: |
| Smoke | 2.66 tok/s, 4 output tokens |
| Rust light | 24.84 tok/s, 95 output tokens |
| Code review | 24.23 tok/s, 111 output tokens |

## Artifacts

```text
docs/ai-workstation/qwen38-performance/results/artifacts/flashnext-iq4xs-benchmark-20260907/
docs/ai-workstation/qwen38-performance/results/artifacts/flashnext-iq4xs-clean-confirmation-20260907-193234/
```

The artifact folder includes:

- `benchmark-summary.json`
- baseline and strict-system variant folders
- generated candidate and repaired Python modules
- hidden/adversarial test outputs
- standard benchmark outputs
- per-variant system snapshots

## Runtime State After Test

IQ4_XS was promoted as the current Hermes experimental manual-test default:

- default model: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`
- active service: `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`
- service state: enabled and active
- IQ3_M service: disabled after promotion
- Discord profile route: updated to use IQ4_XS so it does not point at the stopped IQ3_M backend

Keep `qwen3.8-27b-uncensored-orcarouter-q4_k_m` as the lower-VRAM quality
rollback and `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` as the smaller
Flash-Next rollback.
