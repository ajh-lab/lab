# AI Workstation Automation

This folder tracks automation and runbooks for the Fedora AI workstation (`192.168.1.123`).

## Strix Halo Backend Source

Backend source of truth for ROCm/Vulkan llama.cpp toolboxes:

- GitHub: `https://github.com/kyuz0/amd-strix-halo-toolboxes`
- Remote clone path on workstation: `/mnt/ai/llama/amd-strix-halo-toolboxes`
- Provisioned toolbox container: `llama-rocm-7.2.2`
- Toolbox image: `docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.2.2`

## Script

- `scripts/sync-strix-halo-backend.ps1`
  - Pulls latest upstream repo on workstation
  - Ensures `llama-rocm-7.2.2` toolbox exists
  - Validates device visibility with `llama-cli --list-devices`

## Required `.env` Keys

- `AI_WORKSTATION_IP`
- `AI_WORKSTATION_USER`
- `AI_WORKSTATION_PASSWORD`
