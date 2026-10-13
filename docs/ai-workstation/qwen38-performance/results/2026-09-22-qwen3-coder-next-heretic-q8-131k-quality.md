# Qwen3-Coder-Next Uncensored Heretic Q8_0 131k Quality Test

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-7.14-q4 llama-server`
Purpose: run the controlled Python telemetry quality benchmark and forced tool-call smoke for `llmfan46/Qwen3-Coder-Next-Uncensored-Heretic-GGUF` Q8_0 after Q6_K failed to reach competitive quality.

## Launch

The test used a transient user unit on port `11460`; no durable Cline/DSH route was changed.

```bash
llama-server \
  --host 127.0.0.1 --port 11460 \
  --alias qwen3-coder-next-uncensored-heretic-q8_0-131072-quality \
  -m /mnt/ai/models/qwen3-coder-next-uncensored-heretic-q8_0/Qwen3-Coder-Next-Uncensored-Heretic-Q8_0.gguf \
  -ngl 99 -c 131072 -b 4096 -ub 2048 -fa on \
  -ctk q8_0 -ctv q8_0 --parallel 1 \
  --jinja --temp 1.0 --top-k 40 --top-p 0.95 --min-p 0 \
  --repeat-penalty 1.05 --no-warmup --no-webui
```

Before launch, `ollama ps` was empty. This run was started immediately after the Q6_K test and was later confirmed to cleanly return VRAM to baseline.

## Resource Use

| Checkpoint | Result |
| --- | --- |
| Health time | 22 seconds |
| VRAM after health | 88,589,152,256 bytes, about 82.5 GiB |
| System RAM after health | about 23 GiB available |
| Swap after health | about 10 GiB used |
| Final cleanup | no `llama-server`, `ollama ps` empty, VRAM returned to baseline, about 754 MiB |

## Tool Calling

Forced OpenAI-compatible tool-call smoke passed.

| Metric | Result |
| --- | --- |
| Tool call count | 1 |
| Tool name | `square_number` |
| Arguments | `{"value":17}` |
| Finish reason | `tool_calls` |
| Elapsed | 1.427 seconds |
| Completion speed | 16.11 tok/s |

## Controlled Quality

The same Python telemetry reducer benchmark used for the earlier model comparisons was run against the direct Q8_0 route.

| Pass | Hidden | Standards | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 10/13 | 1/5 | 11/18 | 34.88 tok/s |
| Repair | 11/13 | 3/5 | 14/18 | 33.12 tok/s |

Main repaired defects:

- Failed deduplication by normalized identity.
- Failed same-timestamp segmentation.
- Accepted timestamp without seconds.
- Rejected lowercase RFC3339 `t`/`z`.

## Decision

Do not promote Qwen3-Coder-Next Uncensored Heretic Q8_0 as the default Cline/DSH model. It matched Q6_K quality at `11/18 -> 14/18`, was slightly slower, and used about 18.7 GB more VRAM at 128k context. The higher quant did not fix the quality gap.

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen3-coder-next-heretic-q8-quality-20260922T1342Z
```
