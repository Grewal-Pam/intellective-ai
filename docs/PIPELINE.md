# Pipeline Automation

This repo now has a minimal automation pipeline for evaluation and release readiness.

## Jobs

1. Dataset ingestion
- `POST /datasets` to register evaluation datasets and cases

2. Evaluation runner
- `POST /pipeline/evaluations/run-queued` to process queued evaluations once
- `python -m backend.pipeline_worker --once` to run the same logic from the command line

3. Release guard
- `GET /pipeline/releases/{prompt_id}` to check whether a prompt is ready for release

## Worker mode

Run the worker continuously:

```bash
python -m backend.pipeline_worker
```

Run a single pass:

```bash
python -m backend.pipeline_worker --once
```

## Release-ready conditions
- prompt must be published
- at least one evaluation must be accepted

## Why this matters
- automates the repetitive evaluation work
- creates a clear gate before release
- gives the UI something real to trigger and display
