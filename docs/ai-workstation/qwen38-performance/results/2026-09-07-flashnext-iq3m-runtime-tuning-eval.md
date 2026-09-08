# Flash-Next OrcaRouter IQ3_M Runtime Tuning Evaluation

Tested: 2026-09-07 14:01-14:28 America/Chicago

This run tested runtime and prompt-side accuracy tweaks before trying another
quant. All variants used the same controlled Python telemetry benchmark,
hidden tests, standards probes, deterministic temperature, and one repair pass
used by the earlier model comparisons.

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

## Results

| Variant | Server flags / prompt change | First score | Repaired score | First speed | Repair speed | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Baseline | `--reasoning off --repeat-penalty 1.15` | 13/18 | 15/18 | 26.71 tok/s | 24.39 tok/s | Original Flash-Next IQ3_M result. |
| Repeat penalty 1.0 | `--reasoning off --repeat-penalty 1.0` | 13/18 | 15/18 | 27.58 tok/s | 25.24 tok/s | Keep. It was slightly faster with no benchmark quality loss. |
| Reasoning on | `--reasoning on --repeat-penalty 1.0` | Invalid | Invalid | 26.79 tok/s | 28.23 tok/s | Reject. Both generations hit the 4096 output-token cap and produced no valid `reconstruct_tracks` module. |
| Strict system prompt | Repeat-penalty 1.0 plus a contract-audit Python implementation system prompt | 14/18 | 16/18 | 27.12 tok/s | 25.54 tok/s | Best Flash-Next tuning result. Use as a profile or prompt-side instruction when possible. |
| Reasoning budget 512 | `--reasoning on --reasoning-format deepseek --reasoning-budget 512 --repeat-penalty 1.0` | 14/18 | 15/18 | 27.27 tok/s | 25.59 tok/s | Reject. It improved some standards behavior but introduced a hidden-test regression for `fix="none"`. |

## Strict System Prompt

```text
You are a meticulous Python 3.11 implementation engineer. Return only valid Python source, with no Markdown and no prose. Silently audit the complete contract before finalizing: accepted mapping protocols, exact keys and scalar types, timestamp/RFC3339 conformance, timezone normalization, sorting, deduplication, segment boundaries, numeric rounding, and large-input determinism. Prefer explicit validation over permissive parsing.
```

The strict prompt repaired result still failed two standards probes:

- accepted a timestamp without required seconds
- rejected lowercase RFC3339 `t` / `z`

## Artifacts

| Variant | Artifact folder |
| --- | --- |
| Baseline | `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-python-telemetry/` |
| Repeat penalty 1.0 | `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-repeat1-python-telemetry/` |
| Reasoning on | `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-reasoning-on-repeat1-python-telemetry/` |
| Strict system prompt | `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-strict-system-repeat1-python-telemetry/` |
| Reasoning budget 512 | `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-07-flashnext-orcarouter-iq3m-64k-reasoning-budget512-repeat1-python-telemetry/` |

## Current Runtime Decision

After testing, the live Flash-Next service was restored to the best runtime-only
mode:

```text
--reasoning off --repeat-penalty 1.0
```

The strict system prompt is not yet globally applied to Hermes. It was a
benchmark prompt-side improvement, not a confirmed service-level configuration
change.
