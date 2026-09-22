# Qwen3.8 Flash Next IQ4_XS 32k No-MTP Quality Retest

Date: 2026-09-22
Host: `ai-workstation-evox2`
Runtime: `toolbox run -c llama-rocm-10.0-qwen38-flash-next llama-server`
Purpose: rerun the 32k OrcaRouter Qwen3.8 Flash Next IQ4_XS no-MTP test with a longer supervised load window after the first 32k attempt was stopped too early to prove load failure.

## Launch

The test used the existing transient user unit on direct port `11460`; no durable Cline, DSH, Hermes, or LiteLLM route was changed.

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

Preflight was clean: no `llama-server`/`llama-cli`, `ollama ps` empty, VRAM baseline about 754,573,312 bytes, about 24 GiB available RAM, and about 10 GiB swap already used.

## Load And Resource Use

This run reached health after waiting longer than the first aborted attempt.

| Checkpoint | Result |
| --- | --- |
| Health time | about 3 minutes 47 seconds |
| Lowest observed available RAM during load | about 420 MiB |
| Highest observed swap during load | about 44,138 MiB |
| Available RAM at health | about 11,250 MiB |
| Swap at health | about 27,413 MiB |
| Post-smoke VRAM | 70,967,668,736 bytes, about 66.1 GiB |
| Post-benchmark VRAM | 71,013,400,576 bytes, about 66.1 GiB |
| Post-benchmark system state | about 9.5 GiB available RAM and 26 GiB swap used |
| Final cleanup | `llama-server` initially survived `systemctl --user stop`; PID was killed directly and VRAM returned to baseline |

## Smokes

Direct text smoke passed.

| Metric | Result |
| --- | --- |
| Reply | `32K_OK` |
| Prompt speed | 51.81 tok/s |
| Generation speed | 21.29 tok/s |

Forced OpenAI-compatible tool-call smoke passed.

| Metric | Result |
| --- | --- |
| Tool call count | 1 |
| Tool name | `square_number` |
| Arguments | `{"value":17}` |
| Finish reason | `tool_calls` |
| Completion speed | 26.78 tok/s |

## Controlled Quality

The same Python telemetry reducer benchmark used for the earlier model comparisons was run against the direct 32k route.

| Pass | Hidden | Standards | Combined | Generation speed |
| --- | ---: | ---: | ---: | ---: |
| First | 13/13 | 0/5 | 13/18 | 25.33 tok/s |
| Repair | 13/13 | 1/5 | 14/18 | 23.34 tok/s |

Main repaired defects:

- Accepted RFC3339 offset containing seconds.
- Accepted timestamp without seconds.
- Accepted compact timezone offset without the required colon.
- Rejected lowercase RFC3339 `t`/`z`.

## Decision

The 32k route can load on the current 96 GiB VRAM / 31 GiB Linux RAM split when given enough time, but it is not a better default than the prior 64k IQ4_XS baseline. Load-time pressure remains severe, generation speed did not improve, and the controlled repaired score regressed to `14/18` compared with the earlier 64k no-MTP baseline of `17/18`.

Do not promote the 32k no-MTP q4k/q8v route as the Cline/DSH default from this result. The lower context may still be useful for narrowly bounded manual experiments, but it does not solve the load-pressure issue and did not preserve the strongest IQ4_XS quality result.

Raw run artifacts are on the workstation under:

```text
/home/helios/benchmarks/qwen38-flashnext-iq4xs-32k-nomtp-quality-20260922T142410Z
```
