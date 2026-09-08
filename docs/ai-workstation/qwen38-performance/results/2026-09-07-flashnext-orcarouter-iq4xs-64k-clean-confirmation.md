# Flash-Next OrcaRouter IQ4_XS 64k Clean Confirmation

Tested: 2026-09-07 19:32-19:36 America/Chicago

This is a follow-up confirmation run for
`qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` after a later Discord route
check found that an Ollama runner had separately loaded
`hermes-qwen3-coder:30b-64k` and consumed about 39 GB of VRAM. That later
two-model state caused IQ4_XS reload failures, but it was not present for this
clean confirmation.

## Preflight

| Item | Value |
| --- | --- |
| Model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Port | `11454` |
| Context | `65536` |
| Health | `{"status":"ok"}` |
| Ollama resident models | None (`ollama ps` empty) |
| VRAM before test | `70,881,472,512` bytes total used; IQ4_XS `llama-server` PID used `70,179,528,704` bytes |
| VRAM after test | `70,896,025,600` bytes total used; IQ4_XS `llama-server` PID used `70,192,369,664` bytes |

## Result

| Pass | Hidden tests | Standards probes | Combined score | Speed |
| --- | ---: | ---: | ---: | ---: |
| First | 13/13 | 0/5 | 13/18 | 27.24 tok/s |
| Repaired | 13/13 | 4/5 | 17/18 | 25.41 tok/s |

The clean run reproduced the same quality result as the original IQ4_XS test:
13/18 first pass and 17/18 after the standard repair cycle. Throughput was
slightly higher than the original 17:55-18:03 run, but close enough to treat as
the same performance band.

The remaining repaired standards failure was still lowercase RFC3339 `t`/`z`.

## Short Benchmark

| Scenario | Result |
| --- | ---: |
| Smoke | 5.91 tok/s, 4 output tokens |
| Rust light | 24.97 tok/s, 95 output tokens |
| Code review | 23.94 tok/s, 105 output tokens |

## Artifacts

```text
docs/ai-workstation/qwen38-performance/results/artifacts/flashnext-iq4xs-clean-confirmation-20260907-193234/
```

The artifact folder includes the generated modules, hidden/adversarial test
outputs, standard benchmark output, service definition, preflight state, and
before/after VRAM snapshots.
