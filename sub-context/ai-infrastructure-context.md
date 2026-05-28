# AI Infrastructure Context

Last updated: 2026-05-01 (America/Chicago)

## Scope

This file is the infrastructure-specific companion to `ai-baseline-context.md`.

## Current Core Infrastructure

- k3s control-plane: `192.168.1.80`
- PostgreSQL VM: `lab-pgsql01` (`192.168.1.216`)
- OpenBao VM: `lab-secrets01` (`192.168.1.25`)
- Wiki.js URL: `https://wikijs.192.168.1.80.sslip.io`

## Source Of Truth

- Network inventory: `network_devices.csv`
- Secrets and connection refs: `.env` + OpenBao (`secret/lab/env/*`, `secret/lab/runtime/*`)
- Kubernetes desired state: `k8s/helm/*`, `k8s/manifests/*`
- Phase 1 execution backlog: `phase1-agent-todo.md`

## Execution Notes For Agents

- Read baseline + this file before making infra changes.
- Resolve credentials from OpenBao first when possible.
- Update repo context files after every durable infra change.
- Keep `.env` out of commits.

## OpenBrain

- URL: `https://openbrain.192.168.1.80.sslip.io`
- Namespace: `openbrain`
- OpenBao secret path: `secret/lab/runtime/openbrain`
- Backing DB: external PostgreSQL + pgvector on `lab-pgsql01` (`192.168.1.216:5432`, DB `openbrain`)
- MCP service: `openbrain-mcp`
- Embedding/chat provider: Ollama at `http://<AI_WORKSTATION_IP>:11434/v1`
