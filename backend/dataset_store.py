from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from .settings import data_dir
except ImportError:  # pragma: no cover
    from settings import data_dir  # type: ignore[no-redef]

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = data_dir()
STORE_PATH = DATA_DIR / "evaluation_datasets.json"
LOCK = threading.Lock()

DEFAULT_STORE: dict[str, list[dict[str, Any]]] = {"datasets": []}


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


def list_datasets() -> list[dict[str, Any]]:
    return load_store()["datasets"]


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    for dataset in list_datasets():
        if dataset["id"] == dataset_id:
            return dataset
    return None


def find_dataset_by_name(name: str) -> dict[str, Any] | None:
    for dataset in list_datasets():
        if dataset.get("name") == name:
            return dataset
    return None


def create_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    store = load_store()
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("cases_must_be_a_list")

    dataset = {
        "id": str(uuid4()),
        "name": payload["name"],
        "description": payload.get("description", ""),
        "source_type": payload.get("source_type", "json"),
        "schema_version": payload.get("schema_version", 1),
        "cases": cases,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": payload.get("actor", "data_engineer"),
    }
    store["datasets"].append(dataset)
    save_store(store)
    return dataset


def update_dataset(dataset_id: str, updater) -> dict[str, Any]:
    store = load_store()
    for index, dataset in enumerate(store["datasets"]):
        if dataset["id"] == dataset_id:
            store["datasets"][index] = updater(dataset)
            save_store(store)
            return store["datasets"][index]
    raise KeyError(dataset_id)
