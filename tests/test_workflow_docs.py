from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / "workflows"


class WorkflowDocsTestCase(unittest.TestCase):
    def test_first_workflow_docs_are_present(self):
        readme = (WORKFLOWS_DIR / "README.md").read_text(encoding="utf-8")
        example = (WORKFLOWS_DIR / "examples" / "prompt_approval_flow_example.md").read_text(encoding="utf-8")

        self.assertIn("Who Can Use It", readme)
        self.assertIn("How It Is Used", readme)
        self.assertIn("Why the End Goal Is Justified", readme)
        self.assertIn("Prompt Approval Flow Example", example)
        self.assertIn("What this workflow is trying to do", example)

    def test_second_workflow_docs_are_present(self):
        readme = (WORKFLOWS_DIR / "README.md").read_text(encoding="utf-8")
        example = (WORKFLOWS_DIR / "examples" / "prompt_evaluation_flow_example.md").read_text(encoding="utf-8")
        spec = (WORKFLOWS_DIR / "prompt_evaluation.yaml" ).read_text(encoding="utf-8")

        self.assertIn("Second Workflow: Prompt Evaluation", readme)
        self.assertIn("evaluation flow example", readme)
        self.assertIn("Prompt Evaluation Flow Example", example)
        self.assertIn("queued", spec)
        self.assertIn("accepted", spec)

    def test_third_workflow_docs_are_present(self):
        readme = (WORKFLOWS_DIR / "README.md").read_text(encoding="utf-8")
        example = (WORKFLOWS_DIR / "examples" / "prompt_release_checklist_flow_example.md").read_text(encoding="utf-8")
        spec = (WORKFLOWS_DIR / "prompt_release_checklist.yaml").read_text(encoding="utf-8")

        self.assertIn("Third Workflow: Prompt Release Checklist", readme)
        self.assertIn("release checklist example", readme)
        self.assertIn("Prompt Release Checklist Flow Example", example)
        self.assertIn("checklist_pending", spec)
        self.assertIn("released", spec)
