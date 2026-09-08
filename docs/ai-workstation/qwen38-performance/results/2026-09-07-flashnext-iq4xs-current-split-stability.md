# Flash-Next OrcaRouter IQ4_XS Current Split Stability

Tested: 2026-09-07 21:28-21:56 America/Chicago

This run followed two hard lockups/kernel-panic style failures on
`ai-workstation-evox2` while the BIOS memory split was still approximately
32 GiB system RAM and 96 GiB UMA/VRAM.

## Recovery State

| Item | Value |
| --- | --- |
| OS | Fedora 43 |
| Kernel | `7.1.9-100.fc43.x86_64` |
| Hardware | GMKtec `NucBox_EVO-X2`, BIOS `EVO-X2 1.12` |
| Memory split | About 30 GiB visible Linux RAM, about 96 GiB visible VRAM |
| Flash-Next IQ4_XS service | `llama-qwen38-flashnext-orcarouter-uncensored-iq4xs.service` |
| Full-offload service state after recovery | Disabled and inactive |
| LiteLLM/Hermes state after recovery | `litellm-*`, `hermes-gateway`, and `hermes-dashboard` active |
| OpenBao helper | `openbao-env-get AI_WORKSTATION_PASSWORD` resolved successfully |

The previous boot and the first reboot both showed repeated AMDGPU command
submission failures:

```text
amdgpu 0000:c6:00.0: [drm] *ERROR* Not enough memory for command submission!
```

The previous boot logged 10,746 copies of that error between 21:17:07 and
21:17:19. During the first post-reboot recovery, the Hermes gateway was also
killed by the OOM killer while Flash-Next IQ4_XS was loading.

## Guarded Runtime Tests

| Test | Flags | Outcome | Peak observed pressure |
| --- | --- | --- | --- |
| Original boot profile | `-ngl 999 -c 65536 -b 1024 -ub 256 -ctk q8_0 -ctv q8_0` | Reproduced unstable memory pressure; backend was disabled to stabilize host | VRAM reached about `102,914,801,664` bytes used; system RAM effectively full; swap around 27-36 GiB used |
| Partial offload | `-ngl 44 -c 65536 -b 512 -ub 128 -ctk q8_0 -ctv q8_0` | Did not reach healthy before manual stop | VRAM about `62,219,748,704` bytes; available RAM fell below 500 MiB; swap climbed past 40 GiB |
| Partial offload | `-ngl 47 -c 65536 -b 512 -ub 128 -ctk q8_0 -ctv q8_0` | Stopped automatically at swap guard threshold before healthy | VRAM about `66,452,512,768` bytes; available RAM fell below 500 MiB; swap exceeded 24 GiB |
| Smaller context, full offload | `-ngl 999 -c 32768 -b 512 -ub 128 -ctk q8_0 -ctv q8_0` | Stopped automatically at swap guard threshold before healthy | VRAM about `69,290,696,704` bytes; available RAM stayed low; swap exceeded 26 GiB |

## Conclusion

For this IQ4_XS Flash-Next build, lowering `-ngl` on the current 32 GiB RAM /
96 GiB VRAM split is not a usable fix. It relieves VRAM pressure, but shifts too
much runtime pressure into the small system-RAM side. Reducing context to 32k
also did not avoid the host-RAM bottleneck before the model reached healthy.

The full-offload 64k profile remains a valid benchmark result from the earlier
clean confirmation, but it is not safe as an auto-start or day-to-day default on
this memory split. Retest Flash-Next IQ4_XS only after changing the BIOS memory
split to provide more system RAM, or keep it as a manually started experiment
with guardrails.
