from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from .settings import data_dir
except ImportError:  # pragma: no cover
    from settings import data_dir  # type: ignore[no-redef]

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = data_dir()
STORE_PATH = DATA_DIR / "prompt_evaluations.json"
LOCK = threading.Lock()

DEFAULT_STORE: dict[str, list[dict[str, Any]]] = {"evaluations": []}


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text(json.dumps(DEFAULT_STORE, indent=2), encoding="utf-8")


def load_store() -> dict[str, Any]:
    _ensure_store()
    with LOCK:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def save_store(store: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK:
        STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")


def list_evaluations() -> list[dict[str, Any]]:
    return load_store()["evaluations"]


def get_evaluation(evaluation_id: str) -> dict[str, Any] | None:
    for evaluation in list_evaluations():
        if evaluation["id"] == evaluation_id:
            return evaluation
    return None


def create_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    store = load_store()
    evaluation = {
        "id": str(uuid4()),
        "prompt_id": payload["prompt_id"],
        "evaluation_dataset": payload["evaluation_dataset"],
        "success_metrics": payload["success_metrics"],
        "state": "queued",
        "results": {},
        "history": [
            {
                "event": "queued",
                "state": "queued",
                "actor": payload.get("actor", "evaluation_owner"),
            }
        ],
    }
    store["evaluations"].append(evaluation)
    save_store(store)
    return evaluation


def update_evaluation(evaluation_id: str, updater) -> dict[str, Any]:
    store = load_store()
    for index, evaluation in enumerate(store["evaluations"]):
        if evaluation["id"] == evaluation_id:
            store["evaluations"][index] = updater(evaluation)
            save_store(store)
            return store["evaluations"][index]
    raise KeyError(evaluation_id)
