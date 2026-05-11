from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import time
from urllib.parse import urlparse

try:
    from . import evaluation_store, workflow_store
    from .settings import get_int_setting, get_setting
    from .model_adapter import get_default_adapter
    from .observability import metrics, observe_request
except ImportError:  # pragma: no cover
    import evaluation_store  # type: ignore[no-redef]
    import workflow_store  # type: ignore[no-redef]
    from settings import get_int_setting, get_setting  # type: ignore[no-redef]
    from model_adapter import get_default_adapter  # type: ignore[no-redef]
    from observability import metrics, observe_request  # type: ignore[no-redef]

HOST = get_setting("INTELLECTIVE_AI_HOST", "127.0.0.1")
PORT = get_int_setting("INTELLECTIVE_AI_PORT", 8000)
BASE_DIR = Path(__file__).resolve().parent.parent


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

    method = getattr(handler, "_request_method", "UNKNOWN")
    path = getattr(handler, "_request_path", handler.path)
    start_time = getattr(handler, "_request_start", time.perf_counter())
    observe_request(method, path, status, start_time)


def _read_json(handler: BaseHTTPRequestHandler) -> dict:
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw_body = handler.rfile.read(content_length) if content_length else b"{}"
    return json.loads(raw_body.decode("utf-8"))


def _required_fields(payload: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if not payload.get(field)]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._request_method = "GET"
        self._request_path = urlparse(self.path).path
        self._request_start = time.perf_counter()
        path = urlparse(self.path).path
        if path == "/health":
            return _json_response(self, 200, {"status": "ok"})
        if path == "/metrics":
            body = metrics.render_prometheus().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            observe_request("GET", path, 200, self._request_start)
            return
        if path == "/workflow/prompt-approval":
            workflow_path = BASE_DIR / "workflows" / "prompt_approval.yaml"
            with open(workflow_path, "r", encoding="utf-8") as file_handle:
                return _json_response(self, 200, {"workflow": file_handle.read()})
        if path == "/prompts":
            return _json_response(self, 200, {"prompts": workflow_store.list_prompts()})
        if path == "/evaluations":
            return _json_response(self, 200, {"evaluations": evaluation_store.list_evaluations()})
        if path.startswith("/prompts/"):
            prompt_id = path.split("/", 2)[2]
            prompt = workflow_store.get_prompt(prompt_id)
            if prompt is None:
                return _json_response(self, 404, {"error": "prompt_not_found"})
            return _json_response(self, 200, {"prompt": prompt})
        if path.startswith("/evaluations/"):
            evaluation_id = path.split("/", 2)[2]
            evaluation = evaluation_store.get_evaluation(evaluation_id)
            if evaluation is None:
                return _json_response(self, 404, {"error": "evaluation_not_found"})
            return _json_response(self, 200, {"evaluation": evaluation})
        return _json_response(self, 404, {"error": "not_found"})

    def do_POST(self):
        self._request_method = "POST"
        self._request_path = urlparse(self.path).path
        self._request_start = time.perf_counter()
        path = urlparse(self.path).path
        if path == "/prompts":
            payload = _read_json(self)
            missing = _required_fields(payload, ["name", "content", "use_case", "expected_outcome"])
            if missing:
                return _json_response(self, 400, {"error": "missing_fields", "fields": missing})
            prompt = workflow_store.create_prompt(payload)
            return _json_response(self, 201, {"prompt": prompt})

        if path == "/evaluations":
            payload = _read_json(self)
            missing = _required_fields(payload, ["prompt_id", "evaluation_dataset", "success_metrics"])
            if missing:
                return _json_response(self, 400, {"error": "missing_fields", "fields": missing})
            evaluation = evaluation_store.create_evaluation(payload)
            return _json_response(self, 201, {"evaluation": evaluation})

        if path == "/generate":
            payload = _read_json(self)
            missing = _required_fields(payload, ["prompt"])
            if missing:
                return _json_response(self, 400, {"error": "missing_fields", "fields": missing})
            adapter = get_default_adapter()
            result = adapter.generate(payload["prompt"], payload.get("context"))
            return _json_response(
                self,
                200,
                {"provider": result.provider, "output": result.output},
            )

        if path.startswith("/prompts/"):
            parts = path.strip("/").split("/")
            if len(parts) != 3:
                return _json_response(self, 404, {"error": "not_found"})
            _, prompt_id, action = parts
            payload = _read_json(self)
            prompt = workflow_store.get_prompt(prompt_id)
            if prompt is None:
                return _json_response(self, 404, {"error": "prompt_not_found"})

            def transition_prompt(current_prompt: dict, target_state: str, event: str, actor: str, note: str | None = None):
                if event == "submit" and current_prompt["state"] != "draft":
                    raise ValueError("can_only_submit_from_draft")
                if event == "review" and current_prompt["state"] != "in_review":
                    raise ValueError("can_only_review_from_in_review")
                if event == "revise" and current_prompt["state"] != "rejected":
                    raise ValueError("can_only_revise_from_rejected")
                if event == "publish" and current_prompt["state"] != "approved":
                    raise ValueError("can_only_publish_from_approved")
                current_prompt["state"] = target_state
                current_prompt.setdefault("history", []).append(
                    {
                        "event": event,
                        "state": target_state,
                        "actor": actor,
                        "note": note,
                    }
                )
                if note:
                    current_prompt.setdefault("review_notes", []).append(note)
                return current_prompt

            try:
                if action == "submit":
                    required = _required_fields(payload, ["actor"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = workflow_store.update_prompt(prompt_id, lambda current: transition_prompt(current, "in_review", "submit", payload["actor"]))
                    return _json_response(self, 200, {"prompt": updated})

                if action == "review":
                    required = _required_fields(payload, ["actor", "decision"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    decision = payload["decision"]
                    if decision not in {"approved", "rejected"}:
                        return _json_response(self, 400, {"error": "invalid_decision"})
                    updated = workflow_store.update_prompt(
                        prompt_id,
                        lambda current: transition_prompt(current, decision, "review", payload["actor"], payload.get("note")),
                    )
                    return _json_response(self, 200, {"prompt": updated})

                if action == "revise":
                    required = _required_fields(payload, ["actor"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = workflow_store.update_prompt(prompt_id, lambda current: transition_prompt(current, "draft", "revise", payload["actor"], payload.get("note")))
                    return _json_response(self, 200, {"prompt": updated})

                if action == "publish":
                    required = _required_fields(payload, ["actor", "version_tag"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = workflow_store.update_prompt(
                        prompt_id,
                        lambda current: transition_prompt(current, "published", "publish", payload["actor"], f"version={payload['version_tag']}")
                    )
                    updated["version"] = payload["version_tag"]
                    return _json_response(self, 200, {"prompt": updated})

                return _json_response(self, 404, {"error": "unknown_action"})
            except ValueError as error:
                return _json_response(self, 409, {"error": str(error)})

        if path.startswith("/evaluations/"):
            parts = path.strip("/").split("/")
            if len(parts) != 3:
                return _json_response(self, 404, {"error": "not_found"})
            _, evaluation_id, action = parts
            payload = _read_json(self)
            evaluation = evaluation_store.get_evaluation(evaluation_id)
            if evaluation is None:
                return _json_response(self, 404, {"error": "evaluation_not_found"})

            def transition_evaluation(current_evaluation: dict, target_state: str, event: str, actor: str, note: str | None = None):
                if event == "run" and current_evaluation["state"] != "queued":
                    raise ValueError("can_only_run_from_queued")
                if event == "score" and current_evaluation["state"] != "running":
                    raise ValueError("can_only_score_from_running")
                if event == "revise" and current_evaluation["state"] != "scored":
                    raise ValueError("can_only_revise_from_scored")
                if event == "accept" and current_evaluation["state"] != "scored":
                    raise ValueError("can_only_accept_from_scored")
                current_evaluation["state"] = target_state
                current_evaluation.setdefault("history", []).append(
                    {
                        "event": event,
                        "state": target_state,
                        "actor": actor,
                        "note": note,
                    }
                )
                if note:
                    current_evaluation.setdefault("results", {}).setdefault("notes", []).append(note)
                return current_evaluation

            try:
                if action == "run":
                    required = _required_fields(payload, ["actor"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = evaluation_store.update_evaluation(evaluation_id, lambda current: transition_evaluation(current, "running", "run", payload["actor"]))
                    return _json_response(self, 200, {"evaluation": updated})

                if action == "score":
                    required = _required_fields(payload, ["actor", "results"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})

                    def score_transition(current_evaluation: dict):
                        updated = transition_evaluation(current_evaluation, "scored", "score", payload["actor"], payload.get("note"))
                        updated["results"]["scores"] = payload["results"]
                        return updated

                    updated = evaluation_store.update_evaluation(evaluation_id, score_transition)
                    return _json_response(self, 200, {"evaluation": updated})

                if action == "revise":
                    required = _required_fields(payload, ["actor", "note"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = evaluation_store.update_evaluation(evaluation_id, lambda current: transition_evaluation(current, "needs_revision", "revise", payload["actor"], payload["note"]))
                    return _json_response(self, 200, {"evaluation": updated})

                if action == "accept":
                    required = _required_fields(payload, ["actor", "passing_threshold", "result_summary"])
                    if required:
                        return _json_response(self, 400, {"error": "missing_fields", "fields": required})
                    updated = evaluation_store.update_evaluation(
                        evaluation_id,
                        lambda current: transition_evaluation(current, "accepted", "accept", payload["actor"], payload.get("result_summary")),
                    )
                    updated["results"]["passing_threshold"] = payload["passing_threshold"]
                    updated["results"]["result_summary"] = payload["result_summary"]
                    return _json_response(self, 200, {"evaluation": updated})

                return _json_response(self, 404, {"error": "unknown_action"})
            except ValueError as error:
                return _json_response(self, 409, {"error": str(error)})

        return _json_response(self, 404, {"error": "not_found"})


if __name__ == "__main__":
    print(f"Starting dev server at http://{HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Server stopped")
