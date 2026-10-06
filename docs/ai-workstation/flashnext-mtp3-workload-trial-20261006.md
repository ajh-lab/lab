# Flash Next MTP3 real-workload trial, 2026-10-06

At the owner's request, the ai-workstation route now uses the faster three-token
MTP configuration for supervised real workloads. This supersedes older runtime
status notes for the `qwen3.8-flash-next` alias. The no-MTP setup is retained as
an intact rollback service. This is an owner-selected trial, not completed
long-context or engineering-quality acceptance.

## Active configuration

- Host: `helios@192.168.1.123`, GMKtec EVO-X2, Ryzen AI Max+ 395 / Radeon 8060S,
  128 GB memory, 96 GiB VRAM split; Fedora 43, kernel `7.1.13-100.fc43.x86_64`.
- Manual user unit:
  `llama-qwen38-flashnext-vulkan-inject-262k-q5k-frspec-mtp3-manual.service`.
  Static, `Restart=no`; not enabled for boot.
- Existing trunk: OrcaRouter Qwen3.8 Flash Next Uncensored **IQ4_XS** and its
  F16 vision projector, under `/mnt/ai/models/qwen38-flashnext-orcarouter-uncensored-iq4xs/`.
- Draft: `/mnt/ai/models/qwen38-flashnext-drluoto-mtp-q5k-frspec65k/mtp-Qwen3.8-Flash-Next-Q5_K-frspec-65k.gguf`,
  2700078432 bytes, SHA-256
  `282764bf3ce11b1ff6c715d65b37d7d690eb782734127429d2af6bd72b4c48b9`.
  Source `drluoto/Qwen3.8-Flash-Next-MTP-GGUF`, pinned revision
  `ac875a98457a8effe8fb83de8f3701421f507a24`.
- Runtime: existing Vulkan/RADV binary at
  `/mnt/ai/llama/llama-strix-halo-vulkan-inject-ba5354d/build-vulkan/bin/llama-server`,
  commit `ba5354d46ca63e8225c28e1331f0f7651723ad05` plus the existing local
  quantized-injection graph fallback; build 10718. Toolbox
  `llama-vulkan-radv-qwen38-test`.
- Context **262144**, **one slot**, target F16 K/V, batches **2048/2048**,
  `-ngl 999`, flash attention on, mmap, cache RAM 8192 MiB, reasoning on/low,
  default temperature 1 and repeat penalty 1.0.
- Added flags: `--spec-type draft-mtp`, the draft path above,
  `--spec-draft-ngl 999 --spec-draft-n-max 3 --spec-draft-n-min 1
  --spec-draft-p-min 0.0 --spec-draft-type-k f16 --spec-draft-type-v f16`.
- Direct endpoint remains `http://127.0.0.1:11454/v1`. Internal LiteLLM remains
  `http://127.0.0.1:4004/v1`; authenticated LAN endpoint remains
  `http://192.168.1.123:4000/v1`, model alias **`qwen3.8-flash-next`**.
  Existing clients need no model or endpoint change.
- LAN credential remains OpenBao `secret/homelab/providers/litellm`, field
  `lan_api_key`; no credential was changed.

## Evidence and limits

The benchmark repository owns the detailed
[paired result and exact launch arguments](https://github.com/AJHeitzman/llm-hardware-bench/blob/codex/flashnext-q5k-frspec-mtp-test-20261006/results/2026-10-06/gmktec-evo-x2-flashnext-vulkan-262k-q5k-frspec-mtp-screening.md).
With the same cold-cache requests, three-token drafting measured 41.80 output
tok/s on an 8006-token coding prompt versus 24.79 without MTP, and 39.01 on a
31785-token workflow rewrite versus 24.47. Two-token drafting was slower,
about 37.3 tok/s on both. Prefill did not improve with MTP.

All completed rewrites returned identical YAML. Code outputs hit their
2048-token cap and are not quality passes. The 262144 context allocation was
preserved throughout; occupied contexts above 31785 tokens and Cline/DSH
workloads remain for owner testing. The initial experiment restored and
verified the no-MTP service before the owner requested this trial.

At 19:51 UTC, the MTP3 unit was active with the exact tested argv, one 262144-token slot, speculative decoding enabled, one model process and no Ollama residency. Direct health/model listing, required-mode tool calling, a red-image vision smoke, internal LiteLLM chat and authenticated LAN-listener chat passed. Load to health took 56.25 seconds. After the 60-second observation period, available RAM was 22921 MiB, swap used 6486 MiB and VRAM used 79.71 GiB. The LAN check originated on the workstation. All temporary controllers and RAM guards were stopped after validation. Unit SHA-256: `786b5d3da4b782dbd2f7ad3262100b90847ced432502f14116bb7cd818faf48b`.

## Rollback

The unchanged prior unit is
`llama-qwen38-flashnext-vulkan-inject-262k-low-temp1-manual.service`, with
2048/2048 batches, IQ4_XS, F16 K/V, one 262k slot and no MTP. Unit SHA-256:
`b2b3aa26ac4c9dcb07ed199087883a9df9c3212b4b8a7a5e518cea4ee1ec95cd`.
The verified private checkpoint (unit, config, binary/libraries, patched source,
model hashes) remains at
`/home/helios/.local/share/llm-hardware-bench/backups/20261006T185402Z-current-vulkan-b2048-ub2048`.

After allowing any active user request to finish, run on the workstation:

```bash
systemctl --user stop llama-qwen38-flashnext-vulkan-inject-262k-q5k-frspec-mtp3-manual.service
python3 /home/helios/benchmarks/flashnext-q5k-mtp-20261006/recover.py
```

The saved recovery helper refuses overlapping `llama-server` residency,
verifies the original unit hash, starts the no-MTP service under a 2048 MiB
available-RAM guard, and checks health through a 60-second observation period.
Then verify direct health, one 262144 slot with speculative decoding false,
the LiteLLM alias and a client smoke. Do not start both model units together.
The draft file can remain on disk; rollback does not require deleting it.
