# Model Context Protocol (MCP) — Overview for intellective-ai

This document describes a minimal, practical MCP-compatible shim included in this repo and how to use it.

What I added:
- `backend/mcp_shim.py`: a tiny HTTP shim exposing:
  - `POST /mcp/generate` — accepts `{ "prompt": "...", "context": {...} }` and returns `{ "provider": ..., "output": ... }`.
  - `POST /mcp/capabilities` — returns a minimal capability description.
- `examples/mcp_client.py`: a tiny stdlib-only client to call the shim.

Why this helps you learn MCP
- It gives you a runnable server + client to experiment with context exchange and capability discovery without external APIs.
- It lets you practice streaming, auth, and protocol upgrades later.

How to run the shim (local venv):

```bash
# from repo root
python -m backend.mcp_shim
```

Then run the example client in another shell:

```bash
python examples/mcp_client.py
```

Next steps you can try:
- Extend the shim to support streaming responses (WebSockets or SSE).
- Add authentication (API key header) and enforce it in the shim.
- Replace the local adapter with an external provider behind the same API.
- Add tests under `tests/` that spin up the shim and assert protocol behavior.
