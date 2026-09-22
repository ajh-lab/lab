# Qwen3-Coder-Next Uncensored Heretic Q8/Q6 Context Comparison

Date: 2026-09-22
Host: `ai-workstation-evox2` / `helios@192.168.1.123`
Runtime: `toolbox run -c llama-rocm-7.14-q4 llama-server`
Purpose: compare `llmfan46/Qwen3-Coder-Next-Uncensored-Heretic-GGUF` Q8_0 and Q6_K at 262k and 128k context with one model resident at a time.

## Model Files

| Quant | Path | Size | SHA-256 |
| --- | --- | ---: | --- |
| Q8_0 | `/mnt/ai/models/qwen3-coder-next-uncensored-heretic-q8_0/Qwen3-Coder-Next-Uncensored-Heretic-Q8_0.gguf` | 80G | `d516e8ede3a8477e39e5fe8b92ce79bf428aeeb0a4f0cf8b5c65795dd5ff9d38` |
| Q6_K | `/mnt/ai/models/qwen3-coder-next-uncensored-heretic-q6_k/Qwen3-Coder-Next-Uncensored-Heretic-Q6_K.gguf` | 62G | `7b82235501ed8835c0a2137185bf628ce8d45fc4dea3852e7dd2a2047cdfc245` |

## Launch Template

Each case used the same launch shape on port `11460`, varying only the model file, alias, and context:

```bash
toolbox run -c llama-rocm-7.14-q4 llama-server \
  --host 127.0.0.1 --port 11460 \
  --alias <alias> \
  -m <model-file> \
  -ngl 99 -c <context> -b 4096 -ub 2048 -fa on \
  -ctk q8_0 -ctv q8_0 --parallel 1 \
  --jinja --temp 1.0 --top-k 40 --top-p 0.95 --min-p 0 \
  --repeat-penalty 1.05 --no-warmup --no-webui
```

Before each case, all running `llama-*` user services were stopped, resident Ollama models were stopped, and any leftover `llama-server` process was terminated. Final state after the Q6 run returned to baseline with no resident `llama-server` and about 714 MiB VRAM used.

## Standard Tests

Each case ran the same tests:

- Sentinel completion.
- Forced OpenAI-compatible tool call using `/v1/chat/completions`.
- Short coding prompt asking for a Python event summarizer.
- Long synthetic prefill prompt with 72,045 prompt tokens.

Raw artifacts:

- `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-22-qwen3-coder-next-heretic/q8-summary.md`
- `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-22-qwen3-coder-next-heretic/q8-all-results.json`
- `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-22-qwen3-coder-next-heretic/q6-summary.md`
- `docs/ai-workstation/qwen38-performance/results/artifacts/2026-09-22-qwen3-coder-next-heretic/q6-all-results.json`

## Results

| Quant | Context | Load s | Sentinel gen tok/s | Coding gen tok/s | Long prefill tok/s | Long gen tok/s | Tool calls | VRAM after health | Available RAM after health | Swap used after health |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q8_0 | 262144 | 24 | 30.47 | 31.52 | 474.23 | 23.93 | 1 | 86,880 MiB | 23,002 MiB | 10,095 MiB |
| Q8_0 | 131072 | 24 | 31.67 | 31.58 | 474.21 | 24.55 | 1 | 84,479 MiB | 23,464 MiB | 10,095 MiB |
| Q6_K | 262144 | 18 | 35.04 | 35.75 | 444.89 | 25.09 | 1 | 69,024 MiB | 22,986 MiB | 10,094 MiB |
| Q6_K | 131072 | 18 | 34.65 | 35.20 | 443.22 | 24.73 | 1 | 66,623 MiB | 23,502 MiB | 10,093 MiB |

## Notes

- Q8_0 and Q6_K both met the target of roughly 30 tok/s on the short coding prompt.
- Q6_K was faster than Q8_0 on short generation and used about 17.9 GiB less VRAM at 262k, while preserving successful forced tool-call behavior in this narrow smoke.
- Context size from 262k to 128k saved about 2.4 GiB VRAM for both quants in this launch shape.
- The 72k-token long prompt showed strong prefill throughput on both quants, but long-prompt generation dropped into the mid-20 tok/s range.
- This run did not execute the older hidden Python telemetry quality benchmark. Treat these as throughput, load, and basic tool-call compatibility results, not a final coding-quality promotion.
- No model was left loaded after the run.

## Current Read

Q6_K looks like the better first candidate for Cline/DSH testing on this host: it clears the 30 tok/s target, leaves materially more VRAM headroom than Q8_0, and passed the same forced tool-call smoke at both 128k and 262k. Q8_0 is viable but consumes enough VRAM that it is harder to justify unless follow-up quality testing shows a meaningful advantage.
