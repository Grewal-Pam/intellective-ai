from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib import request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import app, workflow_store  # noqa: E402


class WorkflowStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_base_dir = workflow_store.BASE_DIR
        self.original_data_dir = workflow_store.DATA_DIR
        self.original_store_path = workflow_store.STORE_PATH
        workflow_store.BASE_DIR = Path(self.tempdir.name)
        workflow_store.DATA_DIR = Path(self.tempdir.name) / "data"
        workflow_store.STORE_PATH = workflow_store.DATA_DIR / "prompt_approvals.json"

    def tearDown(self):
        workflow_store.BASE_DIR = self.original_base_dir
        workflow_store.DATA_DIR = self.original_data_dir
        workflow_store.STORE_PATH = self.original_store_path
        self.tempdir.cleanup()

    def test_create_prompt_starts_in_draft(self):
        prompt = workflow_store.create_prompt(
            {
                "name": "Support Reply",
                "content": "Draft a helpful reply",
                "use_case": "customer support",
                "expected_outcome": "clear response",
            }
        )

        self.assertEqual(prompt["state"], "draft")
        self.assertEqual(prompt["version"], "0.1.0")
        self.assertEqual(len(workflow_store.list_prompts()), 1)


class ApprovalApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_base_dir = workflow_store.BASE_DIR
        self.original_data_dir = workflow_store.DATA_DIR
        self.original_store_path = workflow_store.STORE_PATH
        workflow_store.BASE_DIR = Path(self.tempdir.name)
        workflow_store.DATA_DIR = Path(self.tempdir.name) / "data"
        workflow_store.STORE_PATH = workflow_store.DATA_DIR / "prompt_approvals.json"
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
        workflow_store.BASE_DIR = self.original_base_dir
        workflow_store.DATA_DIR = self.original_data_dir
        workflow_store.STORE_PATH = self.original_store_path
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

    def test_full_prompt_approval_lifecycle(self):
        status, response = self._json_request(
            "POST",
            "/prompts",
            {
                "name": "Support Reply",
                "content": "Draft a helpful reply",
                "use_case": "customer support",
                "expected_outcome": "clear response",
                "test_examples": [{"input": "Where is my order?", "expected": "polite status update"}],
                "actor": "prompt_author",
            },
        )
        self.assertEqual(status, 201)
        prompt_id = response["prompt"]["id"]
        self.assertEqual(response["prompt"]["state"], "draft")

        status, response = self._json_request("POST", f"/prompts/{prompt_id}/submit", {"actor": "prompt_author"})
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "in_review")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/review",
            {"actor": "prompt_reviewer", "decision": "approved", "note": "Looks good"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "approved")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/publish",
            {"actor": "product_owner", "version_tag": "1.0.0"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "published")
        self.assertEqual(response["prompt"]["version"], "1.0.0")

        status, response = self._json_request("GET", "/prompts")
        self.assertEqual(status, 200)
        self.assertEqual(response["prompts"][0]["state"], "published")

    def test_invalid_transition_returns_conflict(self):
        status, response = self._json_request(
            "POST",
            "/prompts",
            {
                "name": "Support Reply",
                "content": "Draft a helpful reply",
                "use_case": "customer support",
                "expected_outcome": "clear response",
                "actor": "prompt_author",
            },
        )
        prompt_id = response["prompt"]["id"]

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/publish",
            {"actor": "product_owner", "version_tag": "1.0.0"},
        )
        self.assertEqual(status, 409)
        self.assertEqual(response["error"], "can_only_publish_from_approved")

    def test_reject_then_revise_then_publish(self):
        status, response = self._json_request(
            "POST",
            "/prompts",
            {
                "name": "Support Reply",
                "content": "Draft a helpful reply",
                "use_case": "customer support",
                "expected_outcome": "clear response",
                "actor": "prompt_author",
            },
        )
        self.assertEqual(status, 201)
        prompt_id = response["prompt"]["id"]

        status, response = self._json_request("POST", f"/prompts/{prompt_id}/submit", {"actor": "prompt_author"})
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "in_review")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/review",
            {"actor": "prompt_reviewer", "decision": "rejected", "note": "Needs stronger guardrails"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "rejected")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/revise",
            {"actor": "prompt_author", "note": "Added safety language"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "draft")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/submit",
            {"actor": "prompt_author"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "in_review")

        status, response = self._json_request(
            "POST",
            f"/prompts/{prompt_id}/review",
            {"actor": "prompt_reviewer", "decision": "approved", "note": "Now ready"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(response["prompt"]["state"], "approved")


if __name__ == "__main__":
    unittest.main()
