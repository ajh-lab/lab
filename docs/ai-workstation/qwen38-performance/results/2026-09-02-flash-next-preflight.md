# Qwen3.8-Flash-Next Preflight

Date: 2026-09-02 (America/Chicago)

## Objective

Evaluate whether the official `Qwen/Qwen3.8-Flash-Next` release can be run
locally and usefully on `helios@192.168.1.123` without replacing the current
Qwen3.8 27B Q6_K default.

This phase stopped before any model download. The safe preflight criteria were
not met: the official checkpoints are too large for the current host, the
installed ROCm llama.cpp build predates the required GGUF build, and the only
GGUF files with plausible memory fit are low-precision third-party variants.

Supersession note: later on 2026-09-02, upstream published a dedicated Strix
Halo `qwen4exp` runtime and a split AtomicChat Q4_M64 GGUF was downloaded and
attempted. That measured attempt is recorded in
`2026-09-02-flash-next-runtime-attempt.md`; it also rejected Flash-Next for the
current helios memory split because isolated loads were killed by host RAM OOM
before health.

## Official Model Identity

| Item | Value |
| --- | --- |
| Official repo | `Qwen/Qwen3.8-Flash-Next` |
| Repo revision checked | `de4b8e4d43b917e7706784d8bb445c9af86a3540` |
| License | Qwen Community License 1.0 |
| Type | Causal language model with vision encoder |
| HF task | `image-text-to-text` |
| Architecture | `Qwen4ExpForConditionalGeneration` |
| Native context | 262,144 tokens |
| Parameters | 125B main, 6B active per token |
| Extra capacity | 51B n-gram embedding plus 4B MTP |
| Layers | 48 language layers |
| Attention layout | 36 Gated DeltaNet layers plus 12 Qwen Sparse Attention layers |
| Experts | 512 experts; 10 routed plus 1 shared active |
| Official BF16 files | 360,000,192,888 bytes / 335.28 GiB |
| Official FP8 repo | `Qwen/Qwen3.8-Flash-Next-FP8` |
| Official FP8 files | 185,523,317,458 bytes / 172.78 GiB |

Primary references:

- <https://huggingface.co/Qwen/Qwen3.8-Flash-Next>
- <https://github.com/QwenLM/Qwen3.8-Flash-Next>
- <https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next>
- <https://huggingface.co/Qwen/Qwen3.8-Flash-Next/raw/main/LICENSE>

## Live Host State

| Item | Observed value |
| --- | --- |
| Host | `fedora` / `helios@192.168.1.123` |
| OS | Fedora Linux 43 Workstation Edition |
| Kernel | `7.1.9-100.fc43.x86_64` |
| GPU | AMD Radeon 8060S / `gfx1151` |
| GPU allocation | 103,079,215,104 bytes / 96.0 GiB |
| Linux-visible memory | 30 GiB total, 18 GiB available during inventory |
| Disk available | 1.3T on `/mnt/ai` |
| Ollama | `0.21.2` system binary |
| Hermes | `v0.21.0`, upstream `3d81650c` |
| ROCm llama.cpp | build `10540`, commit `07822bddf` |
| Active default | `qwen3.8-27b-uncensored-q6_k` |
| Active service | `llama-qwen38-uncensored-q6k.service` on `127.0.0.1:11446` |
| Q6 health | `{"status":"ok"}` |
| Q4 rollback | Installed, inactive |
| BF16 experiment | Installed, inactive |

The LiteLLM model list still included the existing qwen3-coder aliases,
DeepSeek aliases, Qwen3.8 Q4/BF16/Q6 aliases, and the obliterated Q6 alias.
Hermes profile inventory showed all 14 existing profiles preserved. No shared
configuration was changed.

Non-secret inventory files are on helios under
`/tmp/qwen38-flashnext-inventory-20260902T212033Z`. A temporary systemd unit
dump that duplicated secret-bearing drop-ins was deleted immediately and is
not part of the evidence set.

## Candidate Size Check

| Candidate | Source | Size | Fit assessment |
| --- | --- | ---: | --- |
| Official BF16 | Qwen | 335.28 GiB | Does not fit |
| Official FP8 | Qwen | 172.78 GiB | Does not fit |
| Bartowski Q4_K_M | Third-party GGUF | 111.39 GiB | Does not fit before overhead |
| Bartowski IQ4_XS | Third-party GGUF | 90.97 GiB | Exceeds estimated loaded memory |
| Bartowski IQ3_XS | Third-party GGUF | 85.63 GiB | Very tight, lower quality |
| Bartowski IQ2_M | Third-party GGUF | 74.85 GiB | Plausible fit, low quality |
| Unsloth UD-IQ4_XS | Third-party GGUF | 87.25 GiB | Very tight without MTP |
| Unsloth UD-Q2_K_XL | Third-party GGUF | 73.45 GiB | Plausible fit, low quality |
| Unsloth MTP bundle | Third-party GGUF | 22.93 GiB | Does not fit alongside plausible candidates |

The existing Q6_K baseline is useful for a rough local overhead floor: the
22,430,999,968-byte file loads as 27,386,691,584 bytes at 131,072 context, so
the host adds roughly 4.96 GB beyond file size for that dense model. A minimal
Qwen3.8-Flash-Next 131k Q8 KV estimate for the 12 full-attention layers is
about 1.61 GB. That puts a Q4-class 97.68 GB decimal file beyond the 103.08 GB
GPU allocation once overhead is included, and leaves IQ3-class files with only
a few GB of unproven margin.

These estimates exclude multimodal projector files and MTP unless listed.
Vision use would add another roughly 1.8-2.4 GB. MTP speculative decoding would
add roughly 24.6 GB for the Unsloth bundle and is not viable on this host with
any quality-preserving quant.

## Runtime Support

The active Strix Halo ROCm service uses the `llama-rocm-7.14-q4` toolbox and
llama.cpp build `10540`. The Bartowski GGUF card says its quants were produced
with llama.cpp `b10665` and that newly supported architectures require that
release or newer. Because Qwen3.8-Flash-Next uses the new `qwen4_exp`
architecture, the installed runtime is not a credible target for a large
download test.

The vLLM recipe is also not a practical local route here. It lists the official
FP8 checkpoint at 172.78 GiB, BF16 at 335.28 GiB, and host memory needs of at
least 51 GB plus headroom for n-gram embedding offload. The current Strix Halo
split gives Linux about 30 GiB total memory, and the published validated
examples are multi-GPU systems.

## Decision

Do not download Qwen3.8-Flash-Next for helios yet.

This is not a rejection of the model. The model card and vendor results make it
worth revisiting, especially for coding and tool-use workloads. The current
local host, however, is not ready for a safe and useful isolated evaluation:

1. Official Qwen BF16 and FP8 checkpoints are far above the 96 GiB GPU budget.
2. Quality-preserving GGUFs are also above budget or too tight after overhead.
3. The only plausible-fit GGUFs are IQ2/Q2-class and would be a low-quality
   compromise before benchmarking even starts.
4. The installed ROCm llama.cpp build predates the required Qwen3.8-Flash-Next
   GGUF support.
5. MTP and vision support materially worsen the memory fit.

The best next option is a separate runtime-preparation phase:

1. Build or obtain a side-by-side Strix Halo ROCm llama.cpp runtime at
   `b10665` or newer.
2. Verify it can load only model metadata or a tiny compatible Qwen4-exp test
   artifact without touching the Q6 default.
3. Recalculate memory against an unloaded GPU and choose between Bartowski
   `IQ2_M` and Unsloth `UD-Q2_K_XL` only if a low-precision, text-only
   experiment is acceptable.
4. Keep MTP and vision out of the first local test.

Final state: Qwen3.8 27B Q6_K remained the default and stayed healthy; no model
download, profile change, LiteLLM edit, Hermes edit, or service restart was
performed.
