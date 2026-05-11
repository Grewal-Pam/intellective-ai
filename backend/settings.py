from __future__ import annotations

from pathlib import Path
from typing import Final
import os

REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DOTENV_PATH: Final[Path] = REPO_ROOT / ".env"


def _load_dotenv() -> None:
    if not DOTENV_PATH.exists():
        return

    for raw_line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def get_setting(name: str, default: str) -> str:
    return os.environ.get(name, default)


def get_int_setting(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def data_dir() -> Path:
    return Path(get_setting("INTELLECTIVE_AI_DATA_DIR", str(REPO_ROOT / "data")))
