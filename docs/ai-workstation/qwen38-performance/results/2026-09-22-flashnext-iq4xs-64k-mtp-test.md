# Qwen3.8 Flash-Next IQ4_XS 64k MTP Test

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-10.0-qwen38-flash-next llama-server`
Purpose: test whether native `draft-mtp` improves the current 64k IQ4_XS route enough to replace the no-MTP manual default.

## Launch

The test used a transient user unit on port `11456`; the durable IQ4_XS service file was not changed.

```bash
llama-server \
  --host 127.0.0.1 --port 11456 \
  --alias qwen3.8-flash-next-uncensored-orcarouter-iq4_xs_mtp_64k \
  -m /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf \
  --mmproj /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf \
  -ngl 999 -c 65536 -b 1024 -ub 256 -fa on \
  -ctk q4_0 -ctv q8_0 --parallel 1 \
  --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio \
  --spec-type draft-mtp \
  --spec-draft-model /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq3m/Qwen3.8-Flash-Next-Uncensored-MTP-draft.gguf \
  --spec-draft-ngl 999 \
  --spec-draft-n-max 3 --spec-draft-n-min 1 --spec-draft-p-min 0.1 \
  --spec-draft-type-k q4_0 --spec-draft-type-v q8_0 \
  --no-warmup --no-webui
```

Before launch, `ollama ps` was empty and no `llama-server` / `llama-cli` process was resident.

## Resource Use

| Checkpoint | Result |
| --- | --- |
| Health time | 224 seconds |
| VRAM after health | 74,945,781,760 bytes, about 69.8 GiB |
| System RAM after health | about 10 GiB available |
| Swap after health | about 26 GiB used |
| After quality benchmark | about 7.5 GiB available RAM, about 26 GiB swap used, 75,190,435,840 bytes VRAM |
| Final cleanup | transient unit stopped; no `llama-server`; `ollama ps` empty; VRAM back to baseline |

## Smoke And Timing

| Test | Result |
| --- | --- |
| Direct health | Passed |
| `/props` | `n_ctx=65536`, vision/video true |
| Short chat sentinel | Passed |
| Forced OpenAI-compatible tool call | Passed; returned one `square_number` tool call |
| Short coding generation | 105 completion tokens at 42.41 tok/s; draft acceptance 0.91358 |
| Native coding generation | 111 completion tokens at 38.37 tok/s; draft acceptance 0.80000 |
| Tool-call generation | 27 completion tokens at 39.36 tok/s; draft acceptance 1.00000 |
| Large native prefill | 14,305 prompt tokens took 188.91 s, 75.73 prompt tok/s |

The large prompt confirmed that MTP improves decode but does not solve long prompt prefill. Logs showed prompt processing slowing from about 232 tok/s at 1k tokens to about 76 tok/s by 14k tokens.

## Controlled Quality

The same Python telemetry reducer benchmark used for the earlier IQ4_XS results was run against the direct MTP route.

| Pass | Hidden | Standards | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 13/13 | 0/5 | 13/18 | 34.73 tok/s |
| Repair | 13/13 | 1/5 | 14/18 | 26.96 tok/s |

Compared with the no-MTP IQ4_XS 64k baseline, first-pass speed improved materially, but repaired correctness regressed from 17/18 to 14/18.

## Decision

Do not promote this MTP configuration as the Cline/DSH default. It is faster for short decode, but the repaired quality regression is too large for implementation work. Keep the no-MTP 64k IQ4_XS route as the safer Flash-Next manual default unless a different MTP branch/config reproduces the 17/18 repaired score.

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen38-flashnext-iq4xs-mtp-20260922T124105Z
```
