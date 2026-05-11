from __future__ import annotations

import argparse
import time

try:
    from .pipeline import run_queued_evaluations
    from .settings import get_int_setting
except ImportError:  # pragma: no cover
    from pipeline import run_queued_evaluations  # type: ignore[no-redef]
    from settings import get_int_setting  # type: ignore[no-redef]


def run_once() -> int:
    processed = run_queued_evaluations()
    return len(processed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the intellective-ai evaluation pipeline worker")
    parser.add_argument("--once", action="store_true", help="Run a single polling cycle and exit")
    parser.add_argument("--interval", type=float, default=get_int_setting("INTELLECTIVE_AI_PIPELINE_POLL_SECONDS", 15), help="Polling interval in seconds")
    args = parser.parse_args()

    if args.once:
        count = run_once()
        print(f"Processed {count} queued evaluation(s)")
        return

    while True:
        count = run_once()
        print(f"Processed {count} queued evaluation(s)")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
