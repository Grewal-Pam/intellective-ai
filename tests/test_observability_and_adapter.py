from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import app, model_adapter, observability  # noqa: E402


class ModelAdapterTestCase(unittest.TestCase):
    def test_default_adapter_is_deterministic(self):
        adapter = model_adapter.get_default_adapter()
        result = adapter.generate("Write a brief support reply", "Customer wants an order update")

        self.assertEqual(result.provider, "echo")
        self.assertIn("Prompt: Write a brief support reply", result.output)
        self.assertIn("Context: Customer wants an order update", result.output)
        self.assertIn("Response: This is a local, deterministic placeholder output.", result.output)


class ObservabilityApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_env = os.environ.get("INTELLECTIVE_AI_DATA_DIR")
        os.environ["INTELLECTIVE_AI_DATA_DIR"] = str(Path(self.tempdir.name) / "data")
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

        self.server = app.HTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()
        os.chdir(self.original_cwd)
        if self.original_env is None:
            os.environ.pop("INTELLECTIVE_AI_DATA_DIR", None)
        else:
            os.environ["INTELLECTIVE_AI_DATA_DIR"] = self.original_env
        self.tempdir.cleanup()

    def _json_request(self, method: str, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=5) as response:
            return response.status, response.read().decode("utf-8"), response.headers.get("Content-Type", "")

    def test_generate_and_metrics_endpoints(self):
        status, body, content_type = self._json_request(
            "POST",
            "/generate",
            {"prompt": "Say hello", "context": "in a friendly tone"},
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["provider"], "echo")
        self.assertIn("Say hello", payload["output"])
        self.assertIn("friendly tone", payload["output"])

        status, body, content_type = self._json_request("GET", "/metrics")
        self.assertEqual(status, 200)
        self.assertIn("text/plain", content_type)
        self.assertIn("intellective_ai_http_requests_total", body)
        self.assertIn("intellective_ai_model_adapter_calls_total", body)
        self.assertGreaterEqual(observability.metrics.render_prometheus().count("intellective_ai_http_requests_total"), 1)
