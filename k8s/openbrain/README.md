# OpenBrain MCP Server Image

This folder contains the OpenBrain MCP server source used by the k3s deployment.

- `index.ts`: MCP server implementation (PostgreSQL + pgvector backend)
- `deno.json`: Deno dependencies/tasks
- `Dockerfile`: container build file

The deployment script builds this image and pushes it to the lab registry:

- `192.168.1.15:5000/openbrain-mcp-server:0.1.0`
