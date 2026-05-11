from __future__ import annotations

from typing import Any

try:
    from . import dataset_store, evaluation_store, workflow_store
except ImportError:  # pragma: no cover
    import dataset_store  # type: ignore[no-redef]
    import evaluation_store  # type: ignore[no-redef]
    import workflow_store  # type: ignore[no-redef]

PASSING_THRESHOLD = 0.85
SAFETY_BLOCKLIST = ("ignore safety", "password", "secret", "ssn")


def ingest_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    return dataset_store.create_dataset(payload)


def _resolve_cases(evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    source = evaluation.get("evaluation_dataset")
    if isinstance(source, list):
        return [case for case in source if isinstance(case, dict)]
    if isinstance(source, dict):
        return [source]
    if isinstance(source, str):
        dataset = dataset_store.get_dataset(source) or dataset_store.find_dataset_by_name(source)
        if dataset is not None:
            return [case for case in dataset.get("cases", []) if isinstance(case, dict)]
        return [{"input": source, "expected": source, "expected_keywords": [source]}]
    return []


def _transition_evaluation(current: dict[str, Any], target_state: str, event: str, actor: str, note: str | None = None) -> dict[str, Any]:
    current["state"] = target_state
    current.setdefault("history", []).append(
        {
            "event": event,
            "state": target_state,
            "actor": actor,
            "note": note,
        }
    )
    if note:
        current.setdefault("results", {}).setdefault("notes", []).append(note)
    return current


def _score_case(prompt_content: str, case: dict[str, Any]) -> dict[str, float]:
    content = prompt_content.lower()
    expected_keywords = [str(keyword).lower() for keyword in case.get("expected_keywords", []) if keyword]
    expected_text = str(case.get("expected", "")).lower().strip()

    quality = 0.25
    if expected_keywords and all(keyword in content for keyword in expected_keywords):
        quality = 1.0
    elif expected_text and expected_text in content:
        quality = 0.9
    elif expected_keywords and any(keyword in content for keyword in expected_keywords):
        quality = 0.6

    safety = 1.0
    if any(blocked in content for blocked in SAFETY_BLOCKLIST):
        safety = 0.0

    consistency = 1.0 if len(content.split()) >= 3 else 0.5
    return {"quality": quality, "safety": safety, "consistency": consistency}


def _build_scores(prompt_content: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    per_case = [_score_case(prompt_content, case) for case in cases]
    case_count = len(per_case)
    if case_count == 0:
        return {
            "case_count": 0,
            "quality": 0.0,
            "safety": 0.0,
            "consistency": 0.0,
            "passing_threshold": PASSING_THRESHOLD,
            "passed": False,
        }

    quality = sum(case["quality"] for case in per_case) / case_count
    safety = min(case["safety"] for case in per_case)
    consistency = sum(case["consistency"] for case in per_case) / case_count
    passed = quality >= PASSING_THRESHOLD and safety >= 1.0
    return {
        "case_count": case_count,
        "quality": round(quality, 3),
        "safety": round(safety, 3),
        "consistency": round(consistency, 3),
        "passing_threshold": PASSING_THRESHOLD,
        "passed": passed,
    }


def run_evaluation_once(evaluation_id: str, actor: str = "evaluation_runner") -> dict[str, Any]:
    evaluation = evaluation_store.get_evaluation(evaluation_id)
    if evaluation is None:
        raise KeyError(evaluation_id)

    prompt = workflow_store.get_prompt(evaluation["prompt_id"])
    if prompt is None:
        return evaluation_store.update_evaluation(
            evaluation_id,
            lambda current: _transition_evaluation(
                current,
                "needs_revision",
                "run",
                actor,
                "prompt_not_found",
            ),
        )

    cases = _resolve_cases(evaluation)
    scores = _build_scores(prompt.get("content", ""), cases)

    def score_transition(current: dict[str, Any]) -> dict[str, Any]:
        updated = _transition_evaluation(current, "scored", "run", actor, "pipeline scored evaluation")
        updated.setdefault("results", {})["scores"] = scores
        updated["results"]["dataset_case_count"] = len(cases)
        return updated

    evaluation_store.update_evaluation(evaluation_id, score_transition)
    if scores["passed"]:
        return evaluation_store.update_evaluation(
            evaluation_id,
            lambda current: _transition_evaluation(current, "accepted", "accept", actor, "auto_accepted_by_pipeline"),
        )

    return evaluation_store.update_evaluation(
        evaluation_id,
        lambda current: _transition_evaluation(current, "needs_revision", "revise", actor, "below_threshold"),
    )


def run_queued_evaluations(limit: int | None = None) -> list[dict[str, Any]]:
    queued = [evaluation for evaluation in evaluation_store.list_evaluations() if evaluation.get("state") == "queued"]
    if limit is not None:
        queued = queued[:limit]

    processed: list[dict[str, Any]] = []
    for evaluation in queued:
        processed.append(run_evaluation_once(evaluation["id"]))
    return processed


def assess_release_readiness(prompt_id: str) -> dict[str, Any]:
    prompt = workflow_store.get_prompt(prompt_id)
    if prompt is None:
        return {
            "prompt_id": prompt_id,
            "ready": False,
            "reasons": ["prompt_not_found"],
            "prompt_state": None,
            "accepted_evaluations": 0,
            "latest_evaluation_id": None,
        }

    evaluations = [evaluation for evaluation in evaluation_store.list_evaluations() if evaluation.get("prompt_id") == prompt_id]
    accepted = [evaluation for evaluation in evaluations if evaluation.get("state") == "accepted"]
    latest_accepted = accepted[-1] if accepted else None

    reasons: list[str] = []
    if prompt.get("state") != "published":
        reasons.append("prompt_not_published")
    if not accepted:
        reasons.append("no_accepted_evaluation")

    return {
        "prompt_id": prompt_id,
        "ready": not reasons,
        "reasons": reasons,
        "prompt_state": prompt.get("state"),
        "accepted_evaluations": len(accepted),
        "latest_evaluation_id": latest_accepted["id"] if latest_accepted else None,
        "latest_passing_threshold": latest_accepted.get("results", {}).get("scores", {}).get("passing_threshold") if latest_accepted else None,
    }
