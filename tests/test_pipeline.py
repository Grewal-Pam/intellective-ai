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

from backend import app, dataset_store, evaluation_store, pipeline, workflow_store  # noqa: E402


class PipelineTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

        self._patch_store(dataset_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(dataset_store, "STORE_PATH", dataset_store.DATA_DIR / "evaluation_datasets.json")
        self._patch_store(evaluation_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(evaluation_store, "STORE_PATH", evaluation_store.DATA_DIR / "prompt_evaluations.json")
        self._patch_store(workflow_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(workflow_store, "STORE_PATH", workflow_store.DATA_DIR / "prompt_approvals.json")


    def _patch_store(self, module, attribute: str, value):
        self._patches = getattr(self, "_patches", [])
        self._patches.append((module, attribute, getattr(module, attribute)))
        setattr(module, attribute, value)

    def _restore_stores(self):
        for module, attribute, value in reversed(getattr(self, "_patches", [])):
            setattr(module, attribute, value)

    def tearDown(self):
        self._restore_stores()
        os.chdir(self.original_cwd)
        self.tempdir.cleanup()

    def test_run_queued_evaluations_auto_accepts_good_prompt(self):
        prompt = workflow_store.create_prompt(
            {
                "name": "Safety prompt",
                "content": "Answer accurately and safely with clear guidance",
                "use_case": "support",
                "expected_outcome": "high quality answer",
            }
        )
        workflow_store.update_prompt(
            prompt["id"],
            lambda current: {**current, "state": "published", "history": current["history"] + [{"event": "publish", "state": "published", "actor": "owner"}]},
        )

        dataset = dataset_store.create_dataset(
            {
                "name": "support-eval",
                "cases": [
                    {"input": "Be accurate", "expected": "accurately", "expected_keywords": ["accurate"]},
                    {"input": "Be safe", "expected": "safely", "expected_keywords": ["safe"]},
                ],
            }
        )
        evaluation = evaluation_store.create_evaluation(
            {
                "prompt_id": prompt["id"],
                "evaluation_dataset": dataset["id"],
                "success_metrics": ["quality", "safety"],
            }
        )

        processed = pipeline.run_queued_evaluations()

        self.assertEqual(len(processed), 1)
        updated = evaluation_store.get_evaluation(evaluation["id"])
        self.assertEqual(updated["state"], "accepted")
        self.assertTrue(updated["results"]["scores"]["passed"])

    def test_release_readiness_requires_published_prompt_and_acceptance(self):
        prompt = workflow_store.create_prompt(
            {
                "name": "Release prompt",
                "content": "Deliver accurate and safe responses",
                "use_case": "support",
                "expected_outcome": "good answer",
            }
        )
        readiness = pipeline.assess_release_readiness(prompt["id"])
        self.assertFalse(readiness["ready"])
        self.assertIn("prompt_not_published", readiness["reasons"])

        workflow_store.update_prompt(
            prompt["id"],
            lambda current: {**current, "state": "published", "history": current["history"] + [{"event": "publish", "state": "published", "actor": "owner"}]},
        )

        dataset = dataset_store.create_dataset(
            {
                "name": "release-eval",
                "cases": [{"input": "Give accurate advice", "expected": "accurate", "expected_keywords": ["accurate"]}],
            }
        )
        evaluation_store.create_evaluation(
            {
                "prompt_id": prompt["id"],
                "evaluation_dataset": dataset["id"],
                "success_metrics": ["quality"],
            }
        )

        pipeline.run_queued_evaluations()
        readiness = pipeline.assess_release_readiness(prompt["id"])
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["reasons"], [])


class PipelineApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

        self._patch_store(dataset_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(dataset_store, "STORE_PATH", dataset_store.DATA_DIR / "evaluation_datasets.json")
        self._patch_store(evaluation_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(evaluation_store, "STORE_PATH", evaluation_store.DATA_DIR / "prompt_evaluations.json")
        self._patch_store(workflow_store, "DATA_DIR", Path(self.tempdir.name) / "data")
        self._patch_store(workflow_store, "STORE_PATH", workflow_store.DATA_DIR / "prompt_approvals.json")

        self.server = app.HTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()
        self._restore_stores()
        os.chdir(self.original_cwd)
        self.tempdir.cleanup()

    def _patch_store(self, module, attribute: str, value):
        self._patches = getattr(self, "_patches", [])
        self._patches.append((module, attribute, getattr(module, attribute)))
        setattr(module, attribute, value)

    def _restore_stores(self):
        for module, attribute, value in reversed(getattr(self, "_patches", [])):
            setattr(module, attribute, value)

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

    def test_pipeline_run_queued_endpoint(self):
        prompt = workflow_store.create_prompt(
            {
                "name": "API prompt",
                "content": "Be accurate and safe",
                "use_case": "support",
                "expected_outcome": "helpful answer",
            }
        )
        workflow_store.update_prompt(
            prompt["id"],
            lambda current: {**current, "state": "published", "history": current["history"] + [{"event": "publish", "state": "published", "actor": "owner"}]},
        )
        dataset = dataset_store.create_dataset(
            {
                "name": "api-eval",
                "cases": [{"input": "accurate", "expected": "accurate", "expected_keywords": ["accurate"]}],
            }
        )
        evaluation_store.create_evaluation(
            {
                "prompt_id": prompt["id"],
                "evaluation_dataset": dataset["id"],
                "success_metrics": ["quality"],
            }
        )

        status, response = self._json_request("POST", "/pipeline/evaluations/run-queued", {})
        self.assertEqual(status, 200)
        self.assertEqual(response["count"], 1)

        status, response = self._json_request("GET", f"/pipeline/releases/{prompt['id']}")
        self.assertEqual(status, 200)
        self.assertTrue(response["ready"])


if __name__ == "__main__":
    unittest.main()
