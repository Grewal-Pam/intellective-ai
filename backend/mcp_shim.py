from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import time

try:
    from .model_adapter import get_default_adapter
    from .settings import get_int_setting, get_setting
except ImportError:  # pragma: no cover
    from model_adapter import get_default_adapter  # type: ignore
    from settings import get_int_setting, get_setting  # type: ignore


HOST = get_setting("INTELLECTIVE_AI_HOST", "127.0.0.1")
PORT = get_int_setting("MCP_SHIM_PORT", 8700)


class MCPHandler(BaseHTTPRequestHandler):
    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _write_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        path = self.path
        if path == "/mcp/generate":
            payload = self._read_json()
            prompt = payload.get("prompt")
            context = payload.get("context")
            if not prompt:
                return self._write_json(400, {"error": "missing_prompt"})
            adapter = get_default_adapter()
            # Sync generate — MCP shim can be extended to stream later
            start = time.perf_counter()
            result = adapter.generate(prompt, context)
            duration = (time.perf_counter() - start) * 1000.0
            return self._write_json(200, {"provider": result.provider, "output": result.output, "duration_ms": duration})

        if path == "/mcp/capabilities":
            # minimal capability discovery
            cap = {"streaming": False, "max_tokens": None, "provider": "local-shim"}
            return self._write_json(200, cap)

        return self._write_json(404, {"error": "not_found"})


def run():
    server = HTTPServer((HOST, PORT), MCPHandler)
    print(f"MCP shim running on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run()
