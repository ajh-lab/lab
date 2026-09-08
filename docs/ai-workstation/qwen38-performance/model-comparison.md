# AI Workstation Model Comparison

Last updated: 2026-09-08 (America/Chicago)

This is the quick comparison table for the recent AI workstation model tests on
`ai-workstation-evox2` / `helios@192.168.1.123`. It summarizes both speed and
the controlled Python telemetry coding benchmark, because decoder speed did not
track directly with implementation quality.

## Current Hermes Default

| Item | Current value |
| --- | --- |
| Default model alias | `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` |
| Active service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` active on port `11454` |
| Context window | `65536` |
| Active runtime flags | `-ngl 999 -c 65536 -b 1024 -ub 256 -fa on -ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off --temp 0 --repeat-penalty 1.0 -lm dio --no-warmup --no-webui` |
| Runtime route | LiteLLM `http://127.0.0.1:4004/v1` -> llama.cpp `http://127.0.0.1:11454/v1` |
| Runtime state checked | Verified active on 2026-09-08 after returning to the observed 96 GiB VRAM / 31 GiB Linux RAM split; direct health, direct smoke, LiteLLM smoke, and the controlled telemetry benchmark passed |
| Experimental routes | IQ3_M on port `11453` remains configured; `UD-IQ3_XXS` on port `11455` remains the safer 8 GiB-floor Flash-Next fallback; Q4 rollback remains configured on port `11448` |
| Current VRAM used at verification | Total ROCm VRAM allocation about 70.9 GB after load |
| Autostart posture | Disabled for all tested large llama.cpp model services; IQ4_XS is active now for manual Hermes testing only |

## Model Decision Table

| Model / route | What it is | Context tested | Loaded VRAM | Observed speed | Controlled coding score | Current decision |
| --- | --- | ---: | ---: | --- | --- | --- |
| `qwen3.8-flash-next-unsloth-ud-iq3_xxs` | Unsloth Qwen3.8 Flash-Next `UD-IQ3_XXS` split GGUF, matching the low-context quant family from the reference video/screenshot | 16k post-BIOS | About 53.9 GB total VRAM allocated; `llama-server` about 53.4 GB. Minimum available RAM during load stayed about 15.8 GiB with an 8 GiB floor; settled at about 26 GiB available RAM after benchmark. | Controlled telemetry: 23.16 tok/s first, 19.91 tok/s repair; short standard coding smokes: 21.84-21.92 tok/s | 5/18 first, 16/18 repaired | Safer Flash-Next fallback when the 8 GiB RAM floor matters. First-pass quality was weak, but repaired quality was closer to the stronger baselines. |
| `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs` | OrcaRouter Qwen3.8 Flash-Next Uncensored `IQ4_XS` split GGUF, loaded with the Flash-Next ROCm toolbox | 64k benchmarked on 96 GiB VRAM; 32k RAM-floor retest failed during load; 64 GiB VRAM fit-mode retest loaded but regressed | Clean benchmark on the larger-VRAM split loaded around 71.1 GB decimal VRAM. The 2026-09-08 original-flags retest on the 96 GiB VRAM / 31 GiB Linux RAM split loaded at about 70.9 GB VRAM, but startup dipped to 518 MiB available RAM and used up to about 39.9 GiB swap. On the 64 GiB VRAM / 62 GiB Linux RAM split, full offload failed allocating KV cache after filling VRAM; fit mode reached health using about 67.0 GB VRAM. | Original telemetry: 26.92 tok/s first, 24.88 tok/s repair; clean confirmation with Ollama unloaded: 27.24 tok/s first, 25.41 tok/s repair; 2026-09-08 original-flags retest: 26.18 tok/s first, 25.24 tok/s repair; short retest smokes: 24.34-24.78 tok/s | Earlier clean 13/18 first, 17/18 repaired; 2026-09-08 original-flags retest 13/18 first, 17/18 repaired; 64 GiB fit-mode 12/18 first, 13/18 repaired | Current manual Hermes test default for hands-on testing on the 96 GiB VRAM split. Quality is reproduced, but autostart remains disabled because startup RAM pressure is extreme. |
| `qwen3.8-flash-next-uncensored-orcarouter-iq3_m` | OrcaRouter Qwen3.8 Flash-Next Uncensored `IQ3_M` split GGUF, loaded with the Flash-Next ROCm toolbox | 64k benchmarked; 131k smoke-tested; post-BIOS 64k RAM-floor retry passed only after lowering the floor to 4 GiB | 64k loaded about 63.3 GB decimal VRAM on the old split. After the 64 GiB VRAM / 62 GiB Linux RAM BIOS split, the 8 GiB-floor guarded load dropped to about 5541 MiB before health and was stopped. The 4 GiB-floor retry reached health with a 4535 MiB minimum and settled around 62.6-62.7 GB VRAM with about 28-30 GiB available host RAM after generation. | Baseline telemetry: 26.71 tok/s first, 24.39 tok/s repair; repeat-penalty 1.0 telemetry: 27.58 tok/s first, 25.24 tok/s repair; post-BIOS 4 GiB-floor telemetry: 27.68 tok/s first, 23.67 tok/s repair; short standard 4 GiB-floor runs: 25.99-26.39 tok/s | Earlier baseline 13/18 first, 15/18 repaired; strict system prompt 14/18 first, 16/18 repaired; post-BIOS 4 GiB-floor run 12/18 first, 13/18 repaired | Configured manual experiment. It loads and runs at 64k with a 4 GiB floor on the 64 GiB VRAM split, but it is no longer the Hermes default. |
| `qwen3.8-27b-uncensored-orcarouter-q4_k_m` | OrcaRouter-derived Qwen3.8 27B Uncensored `Q4_K_M` GGUF | 131k and 64k | About 21.4-22.2 GB at 131k; about 19.7 GB at 64k | 64k telemetry: 11.59 tok/s first, 11.11 tok/s repair; short standard smoke 11.04-11.88 tok/s | 14/18 first, 17/18 repaired at both 131k and 64k | Lower-VRAM quality rollback. Best 27B correctness result so far on the telemetry benchmark, but much slower than Flash-Next IQ4_XS. |
| `qwen3.8-27b-uncensored-q6_k-mtp` | JonathanColetti Qwen3.8 27B Uncensored `Q6_K` target with separate `draft-Q4_0` MTP sidecar | 64k | About 26.9 GB decimal total; `llama-server` about 26.1 GB | About 20.2-20.5 tok/s on telemetry generations; 16.8-22.1 tok/s on short standard coding smoke | 5/18 first, 6/18 repaired | Rejected after manual test setup. Fast decode, but poor controlled coding result; do not promote as quality baseline. |
| `qwen3.8-27b-uncensored-q6_k` | JonathanColetti Qwen3.8 27B Uncensored `Q6_K` GGUF | 131k and 64k | About 27.4-27.5 GB at 131k; about 24.9 GB at 64k | 64k telemetry: 9.00 tok/s first, 8.79 tok/s repair; short standard smoke 8.00-8.88 tok/s | 14/18 first, 16/18 repaired at both 131k and 64k | Quality fallback. Slower and slightly lower repaired score than OrcaRouter Q4_K_M, but still a solid non-MTP baseline. |
| `qwen3.8-27b-uncensored-q4_k_m` | JonathanColetti Qwen3.8 27B Uncensored `Q4_K_M` GGUF | 131k | About 22.2 GB | About 11.5-11.9 tok/s on standard coding runs | 13/18 first, 16/18 repaired | Practical local implementation fallback. Faster than Q6, slightly weaker first-pass result on this benchmark. |
| `qwen3.8-27b-uncensored-q4_k_m-mtp` | Same base Q4 target with separate `draft-Q4_0` MTP sidecar | 64k currently, originally 131k | About 21.3-24.2 GB depending on context | About 16.5-21.8 tok/s decode; large Hermes histories still cause slow first-token latency | 13/18 first, 7/18 repaired | Previous interactive test default. Much faster decode, but worse controlled repair behavior; do not treat speed as quality evidence. |
| `hermes-qwen3-coder:30b-128k` | Ollama Qwen3-Coder 30B-A3B `Q8_0` via LiteLLM | 131k | About 45.8 GB | Fastest tested: both telemetry generations finished in about 111 s total | 10/18 first, 12/18 repaired | Use for low-risk, heavily tested, mechanical coding and documentation. Not the general correctness winner. |
| `qwen3.8-27b-uncensored-bf16` | JonathanColetti Qwen3.8 27B Uncensored BF16 GGUF | 131k | About 57.6-57.7 GB | About 4.1 tok/s | 10/18 first, 14/18 repaired | Do not promote. Higher precision was slower and less correct on this task. Keep for controlled experiments only. |
| `qwen3.8-flash-next-ad-q4_k_m_m64` | AtomicChat Qwen3.8-Flash-Next split `AD-4.27bpw-Q4_K_M-M64` GGUF | Intended 131k | Saw about 55.7 GB VRAM before failure | No valid speed result | Not run; model never reached health | Rejected on current memory split. Load attempts died with host RAM OOM/status 137 before smoke or benchmark. |

## Controlled Coding Benchmark

The main implementation-quality test is the blind Python telemetry reducer:

- standard-library-only Python module
- strict schema and scalar validation
- RFC3339 parsing and UTC normalization
- duplicate detection, deterministic sorting, segmentation, distance/speed, and exact output schema
- 13 hidden behavioral tests
- 5 additional mapping/RFC3339 standards probes
- one identical repair cycle using only two reported failures

| Model / route | First hidden | First standards | First combined | Repaired hidden | Repaired standards | Repaired combined | Main defect after repair |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Flash-Next OrcaRouter IQ4_XS 64k | 13/13 | 0/5 | 13/18 | 13/13 | 4/5 | 17/18 | Rejected lowercase RFC3339 `t`/`z`. |
| Flash-Next OrcaRouter IQ4_XS 64k, clean confirmation | 13/13 | 0/5 | 13/18 | 13/13 | 4/5 | 17/18 | Reproduced the original IQ4_XS result with `ollama ps` empty and only IQ4_XS resident in VRAM. |
| Flash-Next OrcaRouter IQ4_XS 64k, 96 GiB original-flags retest | 13/13 | 0/5 | 13/18 | 13/13 | 4/5 | 17/18 | Reproduced the clean IQ4_XS score after restoring the 96 GiB VRAM split and `-b 1024 -ub 256` full-offload flags. |
| Flash-Next OrcaRouter IQ4_XS 64k, post-BIOS fit no-floor | 12/13 | 0/5 | 12/18 | 12/13 | 1/5 | 13/18 | Fit/spill mode failed same-timestamp segmentation and retained most RFC3339 standards defects. |
| Flash-Next OrcaRouter IQ4_XS 64k, strict system prompt | 13/13 | 1/5 | 14/18 | 10/13 | 4/5 | 14/18 | Repair overcorrected valid RFC3339 offsets and regressed hidden behavior. |
| Flash-Next OrcaRouter IQ3_M 64k | 13/13 | 0/5 | 13/18 | 13/13 | 2/5 | 15/18 | Still accepted missing-seconds and compact-offset timestamps, and rejected lowercase RFC3339 `t`/`z`. |
| Flash-Next OrcaRouter IQ3_M 64k, post-BIOS 4 GiB floor | 12/13 | 0/5 | 12/18 | 12/13 | 1/5 | 13/18 | Still failed distance/speed/best-fix behavior, accepted non-RFC3339 timestamp forms, and rejected lowercase RFC3339 `t`/`z`. |
| Flash-Next OrcaRouter IQ3_M 64k, strict system prompt | 13/13 | 1/5 | 14/18 | 13/13 | 3/5 | 16/18 | Still accepted missing-seconds timestamps and rejected lowercase RFC3339 `t`/`z`. |
| Flash-Next OrcaRouter IQ3_M 64k, `ngram-mod` | 13/13 | 0/5 | 13/18 | 13/13 | 2/5 | 15/18 | Same repaired defects as the live repeat-penalty 1.0 run; speed improved only on the long repair prompt. |
| OrcaRouter Q4_K_M | 13/13 | 1/5 | 14/18 | 13/13 | 4/5 | 17/18 | Rejected lowercase RFC3339 `t`/`z`. |
| OrcaRouter Q4_K_M 64k | 13/13 | 1/5 | 14/18 | 13/13 | 4/5 | 17/18 | Rejected lowercase RFC3339 `t`/`z`; matched 131k quality. |
| Q6_K + MTP draft | 5/13 | 0/5 | 5/18 | 5/13 | 1/5 | 6/18 | Retained broad `segs`/`dlambda` runtime failures and rejected lowercase RFC3339 `t`/`z`. |
| Q6_K | 13/13 | 1/5 | 14/18 | 13/13 | 3/5 | 16/18 | Still accepted missing-seconds and compact-offset timestamps. |
| Q6_K 64k | 13/13 | 1/5 | 14/18 | 13/13 | 3/5 | 16/18 | Still accepted missing-seconds and compact-offset timestamps; matched 131k quality. |
| Base Q4_K_M | 13/13 | 0/5 | 13/18 | 13/13 | 3/5 | 16/18 | Still accepted missing-seconds and compact-offset timestamps. |
| Q4_K_M + MTP draft | 13/13 | 0/5 | 13/18 | 4/13 | 3/5 | 7/18 | Overcorrected RFC3339 parsing and rejected valid `Z` / `+01:00` timestamps. |
| Qwen3-Coder 30B-A3B Q8_0 | 10/13 | 0/5 | 10/18 | 11/13 | 1/5 | 12/18 | Missed explicit mapping repair and retained numeric/RFC3339 bugs. |
| BF16 | 10/13 | 0/5 | 10/18 | 12/13 | 2/5 | 14/18 | Still mishandled valid `none` fix events and some RFC3339 probes. |
| Flash-Next AD Q4_K_M M64 | Not run | Not run | Not run | Not run | Not run | Not run | Could not load without host RAM OOM. |

## Throughput Snapshot

| Model / route | Representative speed result | Notes |
| --- | --- | --- |
| Flash-Next Unsloth UD-IQ3_XXS 16k | 23.16 tok/s first telemetry generation and 19.91 tok/s repair generation; 21.84-21.92 tok/s on short standard coding smokes | First Flash-Next route validated after the 64 GiB VRAM / 62 GiB Linux RAM BIOS split with an 8 GiB RAM floor. It is stable enough for hands-on testing, but first-pass quality was weak. |
| Flash-Next OrcaRouter IQ4_XS 64k | Original: 26.92 tok/s first telemetry generation and 24.88 tok/s repair generation. Clean confirmation with Ollama unloaded: 27.24 tok/s first and 25.41 tok/s repair. 2026-09-08 96 GiB original-flags retest: 26.18 tok/s first and 25.24 tok/s repair; short retest smokes: 24.34-24.78 tok/s. Post-BIOS 64 GiB fit-mode no-floor run: 25.66 tok/s first and 22.73 tok/s repair. | Full-offload on the 96 GiB VRAM split reproduces the 17/18 repaired score. The 64 GiB VRAM split cannot full-offload IQ4_XS at 64k and the fit-mode score regressed to 13/18 repaired. |
| Flash-Next OrcaRouter IQ3_M 64k | Baseline 26.71 tok/s first telemetry generation and 24.39 tok/s repair generation; repeat-penalty 1.0 27.58 tok/s first and 25.24 tok/s repair; post-BIOS 4 GiB-floor run 27.68 tok/s first and 23.67 tok/s repair; 25.99-26.39 tok/s on short standard coding smokes in the 4 GiB-floor run | Loaded successfully on 2026-09-08 only after lowering the post-BIOS RAM floor to 4 GiB. MTP smoke was slower than no-MTP on the tiny prompt, so the active service is no-MTP. |
| Flash-Next OrcaRouter IQ3_M 64k with `ngram-mod` | 27.61 tok/s first telemetry generation; 54.51 tok/s repair generation; short benchmark did not improve broadly | Biggest speed upside from config sweep, but mainly on long repeated repair prompts. Not promoted yet. |
| Q6_K + MTP draft | 20.46 tok/s first telemetry generation; 20.17 tok/s repair generation | Fast but poor quality on the controlled task: 5/18 first, 6/18 repaired. Rejected as default. |
| Q4_K_M + MTP draft | 21.11 tok/s first telemetry generation; 21.76 tok/s repair generation | Decode is fast. Hermes can still feel slow when a chat sends tens of thousands of prompt tokens. |
| OrcaRouter Q4_K_M 64k | 11.59 tok/s first telemetry generation; 11.11 tok/s repair generation | Same 14/18 -> 17/18 quality as 131k, with about 19.7 GB loaded VRAM. |
| OrcaRouter Q4_K_M | 11.37-11.89 tok/s on standard Rust/code-review runs | Best scoring model on the controlled coding task. |
| Q6_K 64k | 9.00 tok/s first telemetry generation; 8.79 tok/s repair generation | Same 14/18 -> 16/18 quality as 131k, with about 24.9 GB loaded VRAM. |
| Base Q4_K_M | 11.48-11.91 tok/s before `--no-mmap`; similar after `--no-mmap` | Fast practical fallback. |
| Q6_K | About 8.9-9.2 tok/s on telemetry generations | Better first-pass score than base Q4, but slower. |
| Qwen3-Coder 30B-A3B Q8_0 | 58.123 s first generation; 53.121 s repair generation | Fastest wall-clock coding benchmark, but lower correctness. |
| BF16 | 4.08-4.21 tok/s standard coding runs | Too slow and did not improve correctness. |
| Flash-Next AD Q4_K_M M64 | No valid result | Killed by host RAM OOM before health. |

## Runtime And Tuning Notes

| Experiment | Result | Decision |
| --- | --- | --- |
| Flash-Next OrcaRouter IQ3_M with 64k context | Initial load attempts were killed by host RAM OOM until a 64 GiB disk-backed swap file was added under `/mnt/ai/swap/`. With swap active, the no-MTP route reached health on port `11453` and passed direct plus LiteLLM smoke. It scored 13/18 first and 15/18 repaired on the controlled benchmark. The swap file is now persisted in `/etc/fstab` with `nofail`. | Keep as a manual-only experiment on the current memory split; do not enable as a boot-persistent service. |
| Flash-Next OrcaRouter IQ3_M with 131k context | A transient manual load reached health after about 2 minutes 48 seconds and passed direct/LiteLLM smoke with `n_ctx=131072`. Settled resource use was about 64.3 GB VRAM, 19 GiB host RAM used, and 20 GiB swap used. A later persistent-service transition was not accepted after VRAM pressure near the device limit and AMDGPU/OOM evidence. | Do not set as always-on on the current 32 GiB RAM / 96 GiB VRAM split. Use only during explicit monitored test windows after unloading other large models. |
| Flash-Next OrcaRouter IQ3_M guarded RAM-floor retry on old split | Before the BIOS split change, guarded service starts were attempted with a 12 GiB available-RAM floor. The 131k unit dropped to about 2.5 GiB available before health, a 64k retry with `-b 512 -ub 128` dropped to about 1.3 GiB, and a 16k retry with `-b 256 -ub 64` dropped to about 1.7 GiB. Each attempt was stopped by the guard before health. | Context and batch reductions did not make IQ3_M acceptable for the requested 12 GiB system-RAM reserve on the old 32 GiB RAM / 96 GiB VRAM split. |
| Flash-Next OrcaRouter IQ3_M 64k post-BIOS retry | On the observed 64 GiB VRAM / 62 GiB Linux RAM split, IQ3_M was retested at 64k with `-b 512 -ub 128` and an 8 GiB available-RAM floor. The load started from about 57 GiB available RAM and nearly empty VRAM, but dropped to about 5541 MiB available RAM before health and was stopped by the guard. | Still not acceptable as an always-on or hands-on default under the 8 GiB RAM floor. Keep `UD-IQ3_XXS` 16k as the current Flash-Next hands-on test route. |
| Flash-Next OrcaRouter IQ3_M 64k post-BIOS 4 GiB-floor retry | On the same observed 64 GiB VRAM / 62 GiB Linux RAM split, IQ3_M was retested at 64k with the available-RAM floor lowered to 4 GiB. It reached health after 34 seconds, with minimum available RAM about 4535 MiB during load, settled around 30 GiB available host RAM, passed direct and LiteLLM smoke, and completed the standard plus controlled Python telemetry benchmarks. | Temporarily promoted for hands-on testing, but superseded by IQ4_XS. The 2026-09-08 controlled score was only 12/18 first and 13/18 repaired. |
| Flash-Next repeat-penalty 1.0 | Changing from `--repeat-penalty 1.15` to `--repeat-penalty 1.0` kept the same 13/18 first and 15/18 repaired score while improving telemetry throughput to 27.58 tok/s first and 25.24 tok/s repair. | Keep for manual IQ3_M test launches; it is not the current Hermes default. |
| Flash-Next reasoning on | Unbounded `--reasoning on` hit the 4096 output-token cap on both generations and failed to produce a valid `reconstruct_tracks` function. | Reject for this route/benchmark. |
| Flash-Next strict system prompt | A profile/prompt-side contract-audit Python system prompt improved the score to 14/18 first and 16/18 repaired while keeping throughput near the repeat-penalty 1.0 run. | Best Flash-Next tuning result so far, but not yet applied globally in Hermes. |
| Flash-Next reasoning budget 512 | `--reasoning on --reasoning-format deepseek --reasoning-budget 512` scored 14/18 first and 15/18 repaired, but introduced a hidden regression for `fix="none"`. | Reject; accuracy did not beat the strict prompt and repaired quality stayed below the non-reasoning prompt-side result. |
| Flash-Next thread sweep | Explicit `-t 8 -tb 12`, `-t 12 -tb 24`, and `-t 16 -tb 32` all stayed at 13/18 first and 15/18 repaired. Speeds clustered around 27.79-27.92 tok/s first and 25.26-25.32 tok/s repair. | Thread count is not a major limiter on this host; auto/default behavior is already close. |
| Flash-Next batch sweep | `-b 2048 -ub 512` and `-b 4096 -ub 1024` improved speed slightly, up to 28.24 tok/s first and 26.25 tok/s repair, but repaired score dropped to 14/18. | Reject larger batch sizes unless repeated tests prove the score drop was noise. |
| Flash-Next cache/checkpoint and fit sweep | `--cache-ram 32768 --kv-unified --ctx-checkpoints 64` and `--fit on --fit-target 1536` both loaded successfully but did not improve the controlled benchmark. | Do not promote for the current default. |
| Flash-Next `ngram-mod` speculative decoding | `--spec-type ngram-mod --spec-ngram-mod-n-match 24 --spec-ngram-mod-n-min 48 --spec-ngram-mod-n-max 64` preserved the 13/18 first and 15/18 repaired score, held first speed at 27.61 tok/s, and raised the long repair prompt to 54.51 tok/s. Short Rust/code-review prompts did not improve. | Most promising speed candidate for long repeated coding/repair prompts; leave unpromoted until manual Hermes chat validates behavior. |
| Flash-Next OrcaRouter IQ4_XS 64k | Chosen from the OrcaRouter GGUF repo as the next practical quant above IQ3_M. The first load attempt failed because a stale IQ3_M `llama-server` process still held about 62 GB VRAM; after clearing it, IQ4_XS loaded cleanly at about 71.1 GB VRAM and scored 13/18 first, 17/18 repaired. Strict prompt improved first pass to 14/18 but repaired to only 14/18 due RFC3339 overcorrection. | Promoted as current experimental Hermes default. Keep baseline prompt behavior; do not apply the strict coding system prompt to IQ4_XS. |
| Flash-Next OrcaRouter IQ4_XS clean confirmation | A later Discord-route check found Ollama had separately loaded `hermes-qwen3-coder:30b-64k` and was holding about 39 GB of VRAM, which made IQ4_XS reload attempts fail with ROCm OOM. After unloading Ollama, a clean confirmation run with `ollama ps` empty reproduced 13/18 first and 17/18 repaired, with 27.24 tok/s first and 25.41 tok/s repair. | The original IQ4_XS quality result is still valid; keep only one large model resident before future controlled benchmarks. |
| Flash-Next OrcaRouter IQ4_XS current-split stability | After a hard reboot, full-offload IQ4_XS reproduced severe memory pressure and AMDGPU command-submission failures on the 32 GiB RAM / 96 GiB VRAM split. Guarded tests with `-ngl 44`, `-ngl 47`, and full offload at 32k context all failed to reach healthy before hitting RAM/swap guardrails. | Do not use IQ4_XS as an auto-start or daily default on the current split. Retest after assigning more system RAM in BIOS or use the 27B OrcaRouter Q4_K_M rollback. |
| Flash-Next OrcaRouter IQ4_XS clean-slate RAM-floor retest | After deleting the live Kalshi hourly CronJob and setting qwen-coder LiteLLM `keep_alive` to `0s`, a clean-slate 64k manual start reached health and passed LiteLLM smoke, but settled with only about 11 GiB available host RAM and 20 GiB swap used. A 32k retry did not reach health before available RAM dropped to 484 MiB. | Not acceptable for a strict 12 GiB system-RAM floor. Superseded by the 96 GiB VRAM original-flags retest, which restored quality but still has dangerous startup pressure. |
| Flash-Next OrcaRouter IQ4_XS post-BIOS 64k fit/no-floor retest | On the observed 64 GiB VRAM / 62 GiB Linux RAM split, full offload failed before health with a ROCm KV-cache OOM. Removing explicit `-ngl` and using `--fit on --fit-target 1536` reached health after 119 seconds. Load used up to about 28.3 GiB swap, then settled around 30 GiB available RAM and 67.1 GB VRAM after the controlled benchmark. | Historical 64 GiB VRAM result only. This fit/spill mode should not replace the 96 GiB full-offload IQ4_XS result; it scored only 12/18 first and 13/18 repaired. |
| Flash-Next OrcaRouter IQ4_XS 96 GiB original-flags retest | After returning BIOS to the observed 96 GiB VRAM / 31 GiB Linux RAM split, IQ4_XS was reloaded with the original full-offload flags: `-ngl 999 -c 65536 -b 1024 -ub 256`. It reached health after 193 seconds, with minimum available RAM of 518 MiB and maximum swap use of 39897 MiB during load. It settled around 11.7 GiB available RAM, about 20.8 GiB swap used, and 70.9 GB VRAM allocated. The controlled benchmark reproduced 13/18 first and 17/18 repaired. | Current Hermes manual-test default. Keep active for supervised testing only; all model services should remain disabled for autostart because the load phase is too close to host-RAM exhaustion. |
| `--no-mmap` on Q4/BF16 | No speed improvement, but no clear regression | Retained for stability and Strix Halo toolbox guidance. |
| ROCm 10 Q4 retest | Decode/context results effectively equal to ROCm 7.14 | Do not promote just for version freshness. |
| Vulkan RADV Q4 retest | Slower than ROCm for this dense Q4 model | Keep ROCm backend. |
| Batch/microbatch matrix | `2048/512` and `4096/1024` did not materially beat `1024/256` | Keep `-b 1024 -ub 256`. |
| One-boot `amd_iommu=off` test | No meaningful decode or cold-context improvement | Rejected; normal IOMMU remains accepted. |
| MTP with embedded target only | Failed because local Q4 target GGUF had no MTP/draft tensors | Use explicit draft sidecar for this file. |
| MTP 64k context | VRAM dropped from about 24.2 GB to about 21.3 GB; large history still dominates latency | Keep 64k for interactive testing; start fresh chats for fair speed checks. |
| Q6_K MTP 64k context | Loaded with the same separate `draft-Q4_0` sidecar on port `11450`; idle VRAM was about 26.9 GB after unloading Ollama | Works as a route/default, but controlled quality was much worse than non-MTP Q6_K. |
| Non-MTP 64k context retest | Q6_K and OrcaRouter Q4_K_M both matched their 131k controlled scores at 64k while using less VRAM | 64k is acceptable for these non-MTP routes when the task fits inside the smaller context. |

## Practical Takeaways

| Need | Best current candidate | Why |
| --- | --- | --- |
| Highest score on the controlled telemetry task | Flash-Next OrcaRouter IQ4_XS 64k and OrcaRouter 27B Q4_K_M | Both reached 17/18 after the standard repair cycle; IQ4_XS is much faster but uses much more VRAM. |
| Current hands-on test default | Flash-Next OrcaRouter IQ4_XS 64k full-offload on 96 GiB VRAM | Reproduced the 13/18 first and 17/18 repaired quality result with about 25-26 tok/s telemetry throughput. Treat it as supervised/manual only because startup dropped to 518 MiB available RAM and used about 39.9 GiB swap. |
| Current lower-VRAM quality baseline | OrcaRouter Q4_K_M 131k | Same repaired score as IQ4_XS with far lower VRAM use, but much slower decode. |
| Conservative local implementation fallback | Q6_K | Solid 14/18 first attempt and 16/18 after repair, but slower and heavier than OrcaRouter Q4_K_M. |
| Fast low-risk/documentation/scaffolding work | Qwen3-Coder 30B-A3B Q8_0 | Much faster wall-clock, but lower correctness on contract-heavy code. |
| Avoid for now | BF16 and Flash-Next AD Q4_K_M M64 | BF16 was slow and lower scoring; the AtomicChat Flash-Next AD split failed to load under the current host memory split. |
