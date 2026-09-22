# Flash-Next OrcaRouter IQ4_XS 262k Backup, 131k Reduction, And Vision Enablement

Date: 2026-09-17 23:01 America/Chicago

Host: `ai-workstation-evox2` / `helios@192.168.1.123`

## Reason

The live IQ4_XS route was running at 262k context and had become swap-heavy
during interactive use. Before changing the runtime, the active command,
metadata, local model artifacts, and image-processing prerequisites were
captured here so the 262k state can be restored or retested intentionally.

## Backed-Up Pre-Change Runtime

- Active unit: transient `llama-qwen38-flashnext-iq4xs-262k-manual.service`
- Durable 64k service: `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`, inactive and disabled for autostart
- Port: `11454`
- Alias: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`
- Model path: `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf`
- Runtime container: `llama-rocm-10.0-qwen38-flash-next`
- Flags:

```text
--host 127.0.0.1 --port 11454 --alias qwen3.8-flash-next-uncensored-orcarouter-iq4_xs
-m /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf
-ngl 999 -c 262144 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1
--reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui
```

LiteLLM advertised this route with `max_input_tokens: 262144` and
`context_window: 262144` before the reduction.

## Pre-Change Resource Snapshot

- Host RAM: `30 GiB` total, `25 GiB` used, `1.9 GiB` free, `5.5 GiB` available
- Swap: `71 GiB` total, `34 GiB` used
- zram swap: `8.3 GiB` used
- `/mnt/ai/swap/qwen-flashnext-test.swap`: `28.9 GB` used
- Active launcher process matched the 262k command above.

This aligns with the user's observed failure pattern: the 262k route can load
and smoke, but it tends to leave the workstation in a swap-heavy interactive
state. The current hands-on route should use 131k unless a specific long-context
test requires 262k.

## Local Model Artifacts

The local model directory currently contains only the split text model shards:

```text
Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00001-of-00003.gguf 44766155936
Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00002-of-00003.gguf 44735995008
Qwen3.8-Flash-Next-Uncensored-IQ4_XS-00003-of-00003.gguf 7971004256
```

No `mmproj` file was found under `/mnt/ai/models` before this change, so
llama.cpp reported text-only behavior and image processing was not enabled.

## 131k Target State

Target active unit: transient `llama-qwen38-flashnext-iq4xs-131k-manual.service`

Target flags are identical to the backed-up 262k command except:

```text
-c 131072
```

LiteLLM, Hermes, and DSH should advertise `131072` for this model after the
change. Large llama.cpp model services remain disabled for autostart.

## Vision / Image Processing Enablement

The Qwen3.8 Flash-Next family is multimodal, but llama.cpp needs the matching
multimodal projector artifact loaded with `--mmproj` before image requests work.

Initial source checks:

- `orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF` lists `mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf`.
- `unsloth/Qwen3.8-Flash-Next-GGUF` lists public `mmproj-F16.gguf` and `mmproj-BF16.gguf`.
- Public Unsloth HEAD checks showed `mmproj-F16.gguf` at `904004000` bytes and `mmproj-BF16.gguf` at `907542944` bytes, so the expected about-900-MB extra artifact size is accurate for disk and likely close to the added projector memory requirement.

Enabled state on 2026-09-17 23:29 America/Chicago:

- Downloaded matching OrcaRouter projector:
  `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf`
- Source URL:
  `https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF/resolve/main/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf`
- Size: `907543296` bytes.
- SHA-256:
  `f0f352a97a62a057f3aecdb597cac664762cea2ca23f7b16ec92eee28c5572d9`
- GGUF magic verified: `GGUF`.
- Active transient unit restarted with:
  `--mmproj /mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/mmproj-Qwen3.8-Flash-Next-Uncensored-F16.gguf`
- Durable manual service updated to the same 131k vision command and left
  disabled/inactive:
  `/home/helios/.config/systemd/user/llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`
- Durable service backup:
  `/home/helios/.config/systemd/user/backups/iq4xs-vision-131k-20260917-233409/llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service`

Verification:

- Restart health: `ok` after `191s`.
- `/props`: `n_ctx=131072`, `modalities={'vision': True, 'video': True, 'audio': False}`.
- Direct llama.cpp image smoke: generated red PNG returned `Red`.
- LiteLLM image smoke through `http://127.0.0.1:4004/v1`: generated red PNG
  returned `Red`.
- Post-smoke memory snapshot: `30 GiB` RAM total, `20 GiB` used, `8.7 GiB`
  free, `10 GiB` available; `71 GiB` swap total, `26 GiB` used.

The image path is enabled for the active 131k manual route. Keep the route
manual-only; all large llama.cpp services remain disabled for autostart.
