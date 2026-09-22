# Qwen3-Coder-Next Uncensored Heretic Q6_K 131k Quality Test

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-7.14-q4 llama-server`
Purpose: run the controlled Python telemetry quality benchmark and forced tool-call smoke for `llmfan46/Qwen3-Coder-Next-Uncensored-Heretic-GGUF` Q6_K after the earlier throughput-only comparison.

## Launch

The test used a transient user unit on port `11460`; no durable Cline/DSH route was changed.

```bash
llama-server \
  --host 127.0.0.1 --port 11460 \
  --alias qwen3-coder-next-uncensored-heretic-q6_k-131072-quality \
  -m /mnt/ai/models/qwen3-coder-next-uncensored-heretic-q6_k/Qwen3-Coder-Next-Uncensored-Heretic-Q6_K.gguf \
  -ngl 99 -c 131072 -b 4096 -ub 2048 -fa on \
  -ctk q8_0 -ctv q8_0 --parallel 1 \
  --jinja --temp 1.0 --top-k 40 --top-p 0.95 --min-p 0 \
  --repeat-penalty 1.05 --no-warmup --no-webui
```

Before launch, `ollama ps` was empty and no `llama-server` / `llama-cli` process was resident.

## Resource Use

| Checkpoint | Result |
| --- | --- |
| Health time | 19 seconds |
| VRAM after health | 69,865,779,200 bytes, about 65.1 GiB |
| System RAM after health | about 23 GiB available |
| Swap after health | about 10 GiB used |
| After quality benchmark | about 22 GiB available RAM, about 10 GiB swap used, 70,048,358,400 bytes VRAM |
| Final cleanup | initial service stop left a stale closed-port `llama-server`; PID was killed directly and VRAM returned to baseline, about 754 MiB |

## Tool Calling

Forced OpenAI-compatible tool-call smoke passed.

| Metric | Result |
| --- | --- |
| Tool call count | 1 |
| Tool name | `square_number` |
| Arguments | `{"value":17}` |
| Finish reason | `tool_calls` |
| Elapsed | 1.55 seconds |
| Completion speed | 14.84 tok/s |

## Controlled Quality

The same Python telemetry reducer benchmark used for the earlier model comparisons was run against the direct Q6_K route.

| Pass | Hidden | Standards | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 10/13 | 1/5 | 11/18 | 36.60 tok/s |
| Repair | 11/13 | 3/5 | 14/18 | 34.65 tok/s |

Main repaired defects:

- Failed deduplication by normalized identity.
- Failed same-timestamp segmentation.
- Accepted timestamp without seconds.
- Rejected lowercase RFC3339 `t`/`z`.

## Decision

Do not promote Qwen3-Coder-Next Uncensored Heretic Q6_K as the default Cline/DSH model from this result. It is fast and tool calling works, but its controlled quality score is materially behind Flash-Next IQ4_XS no-MTP (`17/18` repaired) and OrcaRouter Q4_K_M (`17/18` repaired).

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen3-coder-next-heretic-q6-quality-20260922T1328Z
```
