from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import app, evaluation_store  # noqa: E402


class EvaluationStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_base_dir = evaluation_store.BASE_DIR
        self.original_data_dir = evaluation_store.DATA_DIR
        self.original_store_path = evaluation_store.STORE_PATH
        evaluation_store.BASE_DIR = Path(self.tempdir.name)
        evaluation_store.DATA_DIR = Path(self.tempdir.name) / "data"
        evaluation_store.STORE_PATH = evaluation_store.DATA_DIR / "prompt_evaluations.json"

    def tearDown(self):
        evaluation_store.BASE_DIR = self.original_base_dir
        evaluation_store.DATA_DIR = self.original_data_dir
        evaluation_store.STORE_PATH = self.original_store_path
        self.tempdir.cleanup()

    def test_create_evaluation_starts_queued(self):
        evaluation = evaluation_store.create_evaluation(
            {
                "prompt_id": "prompt-1",
                "evaluation_dataset": "support-dataset",
                "success_metrics": ["accuracy", "safety"],
            }
        )

        self.assertEqual(evaluation["state"], "queued")
        self.assertEqual(len(evaluation_store.list_evaluations()), 1)


class EvaluationApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_base_dir = evaluation_store.BASE_DIR
        self.original_data_dir = evaluation_store.DATA_DIR
        self.original_store_path = evaluation_store.STORE_PATH
        evaluation_store.BASE_DIR = Path(self.tempdir.name)
        evaluation_store.DATA_DIR = Path(self.tempdir.name) / "data"
        evaluation_store.STORE_PATH = evaluation_store.DATA_DIR / "prompt_evaluations.json"
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
        evaluation_store.BASE_DIR = self.original_base_dir
        evaluation_store.DATA_DIR = self.original_data_dir
        evaluation_store.STORE_PATH = self.original_store_path
        self.tempdir.cleanup()

    def _json_request(self, method: str, path: str, payload: dict | None = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_evaluation_acceptance_flow(self):
        status, response = self._json_request(
            "POST",
            "/evaluations",
            {
                "prompt_id": "prompt-1",
                "evaluation_dataset": "support-dataset",
                "success_metrics": ["accuracy", "safety"],
                "actor": "evaluation_owner",
            },
        )
        self.assertEqual(status, 201)
        evaluation_id = response["evaluation"]["id"]
        self.assertEqual(response["evaluation"]["state"], "queued")

        status, response = self._json_request("POST", f"/evaluations/{evaluation_id}/run", {"actor": "evaluation_owner"})
        self.assertEqual(status, 200)
        self.assertEqual(response["evaluation"]["state"], "running")

        status, response = self._json_request(
            "POST",
            f"/evaluations/{evaluation_id}/score",
            {
                "actor": "evaluation_owner",
                "results": {"accuracy": 0.95, "safety": 1.0, "consistency": 0.9},
                "note": "Strong result",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["evaluation"]["state"], "scored")

        status, response = self._json_request(
            "POST",
            f"/evaluations/{evaluation_id}/accept",
            {
                "actor": "prompt_reviewer",
                "passing_threshold": 0.9,
                "result_summary": "Meets expected quality",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["evaluation"]["state"], "accepted")
        self.assertEqual(response["evaluation"]["results"]["passing_threshold"], 0.9)

    def test_evaluation_revision_flow(self):
        status, response = self._json_request(
            "POST",
            "/evaluations",
            {
                "prompt_id": "prompt-1",
                "evaluation_dataset": "support-dataset",
                "success_metrics": ["accuracy", "safety"],
                "actor": "evaluation_owner",
            },
        )
        evaluation_id = response["evaluation"]["id"]

        status, response = self._json_request("POST", f"/evaluations/{evaluation_id}/run", {"actor": "evaluation_owner"})
        self.assertEqual(status, 200)

        status, response = self._json_request(
            "POST",
            f"/evaluations/{evaluation_id}/score",
            {
                "actor": "evaluation_owner",
                "results": {"accuracy": 0.55, "safety": 0.7, "consistency": 0.6},
            },
        )
        self.assertEqual(status, 200)

        status, response = self._json_request(
            "POST",
            f"/evaluations/{evaluation_id}/revise",
            {"actor": "prompt_reviewer", "note": "Needs stronger examples"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["evaluation"]["state"], "needs_revision")
