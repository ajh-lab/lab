# Qwen3.8 Flash Next Unsloth UD-IQ3_XXS 131k Quality Test

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-10.0-qwen38-flash-next llama-server`
Purpose: test the smaller Unsloth `UD-IQ3_XXS` Flash-Next quant at 131k context on the current 96 GiB VRAM / 31 GiB Linux RAM split.

## Launch

The test used a transient direct route on port `11460`; no durable Cline, DSH, Hermes, or LiteLLM route was changed.

```bash
llama-server \
  --host 127.0.0.1 --port 11460 \
  --alias qwen3.8-flash-next-unsloth-ud-iq3_xxs-131072-quality \
  -m /mnt/ai/models/qwen38-flashnext-unsloth-ud-iq3xxs/UD-IQ3_XXS/Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf \
  -ngl 99 -c 131072 -b 512 -ub 128 -fa on \
  -ctk q8_0 -ctv q8_0 --parallel 1 \
  --reasoning off --temp 0 --repeat-penalty 1.0 \
  -lm dio --no-warmup --no-webui
```

Preflight was clean: no `llama-server`/`llama-cli`, `ollama ps` empty, VRAM baseline about 754,577,408 bytes, and swap at `0B` after the earlier manual swap clear.

Model hash:

```text
268f81fdedf3149a538f252308927a4d5d1f6e062c178568a51e3b519744f8a8  /mnt/ai/models/qwen38-flashnext-unsloth-ud-iq3xxs/UD-IQ3_XXS/Qwen3.8-Flash-Next-UD-IQ3_XXS-00001-of-00003.gguf
```

## Load And Resource Use

| Checkpoint | Result |
| --- | --- |
| Health time | 349 seconds, about 5 minutes 49 seconds |
| Lowest observed available RAM during load | about 432 MiB |
| Highest observed swap during load | about 43,378 MiB |
| Available RAM at health | about 11,436 MiB |
| Swap at health | about 27,153 MiB |
| Post-smoke VRAM | 56,617,918,464 bytes, about 52.7 GiB |
| Post-benchmark VRAM | 56,639,561,728 bytes, about 52.7 GiB |
| Post-benchmark system state | about 9.7 GiB available RAM and 26 GiB swap used |
| Final cleanup | no `llama-server`/`llama-cli`, `ollama ps` empty, VRAM returned to baseline |

## Smokes

Direct text smoke passed.

| Metric | Result |
| --- | --- |
| Reply | `UD131K_OK` |
| Prompt speed | 52.41 tok/s |
| Generation speed | 12.58 tok/s |

Forced OpenAI-compatible tool-call smoke passed.

| Metric | Result |
| --- | --- |
| Tool call count | 1 |
| Tool name | `square_number` |
| Arguments | `{"value":17}` |
| Finish reason | `tool_calls` |
| Prompt speed | 87.21 tok/s |
| Completion speed | 5.71 tok/s |

## Controlled Quality

The same Python telemetry reducer benchmark used for the earlier model comparisons was run against the direct 131k route.

| Pass | Hidden | Standards | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 5/13 | 0/5 | 5/18 | 23.66 tok/s |
| Repair | 5/13 | 2/5 | 7/18 | 23.30 tok/s |

Main first-pass defects:

- Structural `build_segment` runtime error across most normal behavior tests.
- Rejected read-only mapping input.
- Rejected lowercase RFC3339 `t`/`z`.

Main repaired defects:

- Regressed normal RFC3339 timezone handling across many hidden tests.
- Still rejected read-only mapping input.
- Accepted timestamp without seconds.
- Still rejected lowercase RFC3339 `t`/`z`.

## Decision

Do not promote `UD-IQ3_XXS` at 131k on the current 96 GiB VRAM / 31 GiB Linux RAM split. It uses materially less VRAM than IQ4_XS, but it did not avoid dangerous load-time host memory pressure, tool-call generation was slow, and the controlled repaired score collapsed to `7/18`.

This result is worse than the earlier 16k `UD-IQ3_XXS` run, which repaired to `16/18`, and worse than the IQ4_XS 64k no-MTP baseline, which repaired to `17/18`.

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen38-flashnext-ud-iq3xxs-131k-quality-20260922T145755Z
```
