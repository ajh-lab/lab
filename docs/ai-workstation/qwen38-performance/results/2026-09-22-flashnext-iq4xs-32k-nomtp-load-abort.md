# Qwen3.8 Flash Next IQ4_XS 32k No-MTP Load Abort

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-10.0-qwen38-flash-next llama-server`
Purpose: retest OrcaRouter Qwen3.8 Flash Next IQ4_XS without MTP at a smaller 32k context window to see whether the lower context avoided the load-time host memory pressure seen at 64k and 131k.

Superseded by `2026-09-22-flashnext-iq4xs-32k-nomtp-quality-retest.md`. This first run was stopped too early to prove that 32k could not load; the later retest reached health after about 3 minutes 47 seconds, passed smokes, and completed the controlled benchmark.

## Launch

The test used a transient user unit on direct port `11460`; no durable Cline, DSH, Hermes, or LiteLLM route was changed.

```bash
llama-server \
  --host 127.0.0.1 --port 11460 \
  --alias qwen3.8-flash-next-uncensored-orcarouter-iq4_xs-32768-nomtp-quality \
  -m /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf \
  --mmproj /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf \
  -ngl 999 -c 32768 -b 1024 -ub 256 -fa on \
  -ctk q4_0 -ctv q8_0 --parallel 1 \
  --reasoning off --temp 0 --repeat-penalty 1.0 \
  -lm dio --no-warmup --no-webui
```

Before launch, `ollama ps` was empty, no `llama-server`/`llama-cli` process was resident, and VRAM was at baseline around 754,581,504 bytes.

Model/projector hashes captured for this run:

```text
50dc0856abd4a8ecea97a47ffa197bde3ea8d7d0f49d0e1fea7f71c97e8a70d1  /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf
f0f352a97a62a057f3aecdb597cac664762cea2ca23f7b16ec92eee28c5572d9  /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf
```

## Result

The route had not reached health when the run was stopped. After roughly 2.5 minutes, `/health` still returned:

```json
{"error":{"message":"Loading model","type":"unavailable_error","code":503}}
```

Live resource telemetry during the load attempt showed the same dangerous startup pattern as the larger-context IQ4_XS runs:

| Checkpoint | Result |
| --- | --- |
| Health status | Still loading; no successful health response |
| Lowest observed available RAM before abort | about 634 MiB |
| Highest observed swap use before abort | about 37 GiB |
| Observed VRAM during load | 69,304,397,824 bytes, about 64.5 GiB |
| Journal state | still in `load_model` for the IQ4_XS target |
| Controlled benchmark | not run |
| Forced tool-call smoke | not run |

The service was stopped before the host became unstable. Cleanup verification immediately afterward showed no `llama-server`/`llama-cli` process, `ollama ps` empty, VRAM back to baseline around 754,573,312 bytes, and about 24 GiB available system RAM. Swap still reported about 10 GiB used after cleanup, which is consistent with Linux retaining swapped pages until pressure changes.

## Decision

Do not treat 32k context as a proven fix for IQ4_XS on the current 96 GiB VRAM / 31 GiB Linux RAM split. This was an aborted safety run, not proof that 32k cannot load. The smaller context did not avoid the load-time system RAM and swap pressure seen in larger-context runs, and the model was stopped before benchmark traffic.

The useful conclusion is that the current failure mode is dominated by Flash-Next IQ4_XS load-time host memory pressure, not just active context length. Further IQ4_XS retesting should use a materially different lever, such as a smaller quant, a different BIOS memory split, fit/spill mode with explicit quality acceptance, or a lower-risk fallback model.

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen38-flashnext-iq4xs-32k-nomtp-quality-20260922T1406Z
```
