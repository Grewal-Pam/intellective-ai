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
STORE_PATH = DATA_DIR / "prompt_approvals.json"
LOCK = threading.Lock()

DEFAULT_STORE: dict[str, list[dict[str, Any]]] = {"prompts": []}


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


def list_prompts() -> list[dict[str, Any]]:
    return load_store()["prompts"]


def get_prompt(prompt_id: str) -> dict[str, Any] | None:
    for prompt in list_prompts():
        if prompt["id"] == prompt_id:
            return prompt
    return None


def create_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    store = load_store()
    prompt = {
        "id": str(uuid4()),
        "name": payload["name"],
        "content": payload["content"],
        "use_case": payload["use_case"],
        "expected_outcome": payload["expected_outcome"],
        "test_examples": payload.get("test_examples", []),
        "state": "draft",
        "version": payload.get("version", "0.1.0"),
        "review_notes": [],
        "history": [
            {
                "event": "created",
                "state": "draft",
                "actor": payload.get("actor", "prompt_author"),
            }
        ],
    }
    store["prompts"].append(prompt)
    save_store(store)
    return prompt


def update_prompt(prompt_id: str, updater) -> dict[str, Any]:
    store = load_store()
    for index, prompt in enumerate(store["prompts"]):
        if prompt["id"] == prompt_id:
            store["prompts"][index] = updater(prompt)
            save_store(store)
            return store["prompts"][index]
    raise KeyError(prompt_id)
