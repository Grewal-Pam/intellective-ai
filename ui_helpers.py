from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


@dataclass
class ApiResult:
    ok: bool
    status_code: int
    data: dict[str, Any]
    error: str | None = None


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> ApiResult:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
            return ApiResult(True, response.getcode(), data)
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        data = json.loads(raw) if raw else {}
        return ApiResult(False, exc.code, data, error=data.get("error", exc.reason))
    except URLError as exc:
        return ApiResult(False, 0, {}, error=str(exc.reason))


def _request_text(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[bool, int, str]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=10) as response:
            return True, response.getcode(), response.read().decode("utf-8")
    except HTTPError as exc:
        return False, exc.code, exc.read().decode("utf-8")
    except URLError as exc:
        return False, 0, str(exc.reason)


def api_get(base_url: str, path: str) -> ApiResult:
    return _request_json("GET", f"{base_url.rstrip('/')}{path}")


def api_post(base_url: str, path: str, payload: dict[str, Any]) -> ApiResult:
    return _request_json("POST", f"{base_url.rstrip('/')}{path}", payload)


def get_prompts(base_url: str = DEFAULT_BASE_URL) -> list[dict[str, Any]]:
    result = api_get(base_url, "/prompts")
    return list(result.data.get("prompts", [])) if result.ok else []


def get_evaluations(base_url: str = DEFAULT_BASE_URL) -> list[dict[str, Any]]:
    result = api_get(base_url, "/evaluations")
    return list(result.data.get("evaluations", [])) if result.ok else []


def get_metrics(base_url: str = DEFAULT_BASE_URL) -> str:
    ok, _, body = _request_text("GET", f"{base_url.rstrip('/')}/metrics")
    return body if ok else body or "metrics unavailable"


def create_prompt(base_url: str, payload: dict[str, Any]) -> ApiResult:
    return api_post(base_url, "/prompts", payload)


def submit_prompt(base_url: str, prompt_id: str, actor: str) -> ApiResult:
    return api_post(base_url, f"/prompts/{prompt_id}/submit", {"actor": actor})


def review_prompt(base_url: str, prompt_id: str, actor: str, decision: str, note: str = "") -> ApiResult:
    body: dict[str, Any] = {"actor": actor, "decision": decision}
    if note:
        body["note"] = note
    return api_post(base_url, f"/prompts/{prompt_id}/review", body)


def publish_prompt(base_url: str, prompt_id: str, actor: str, version_tag: str) -> ApiResult:
    return api_post(base_url, f"/prompts/{prompt_id}/publish", {"actor": actor, "version_tag": version_tag})


def create_evaluation(base_url: str, payload: dict[str, Any]) -> ApiResult:
    return api_post(base_url, "/evaluations", payload)


def run_evaluation(base_url: str, evaluation_id: str, actor: str) -> ApiResult:
    return api_post(base_url, f"/evaluations/{evaluation_id}/run", {"actor": actor})


def score_evaluation(base_url: str, evaluation_id: str, actor: str, results: dict[str, Any], note: str = "") -> ApiResult:
    body: dict[str, Any] = {"actor": actor, "results": results}
    if note:
        body["note"] = note
    return api_post(base_url, f"/evaluations/{evaluation_id}/score", body)


def run_queued_evaluations(base_url: str, limit: int = 10) -> ApiResult:
    """Run queued evaluations through the pipeline."""
    return api_post(base_url, "/pipeline/evaluations/run-queued", {"limit": limit})


def get_release_readiness(base_url: str, prompt_id: str) -> ApiResult:
    """Check if a prompt is ready for release."""
    return api_get(base_url, f"/pipeline/releases/{prompt_id}")
