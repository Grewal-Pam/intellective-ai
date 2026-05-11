# intellective-ai

[![CI](https://github.com/Grewal-Pam/intellective-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Grewal-Pam/intellective-ai/actions/workflows/ci.yml)

Production-ready scaffold for GenAI, RAG, and prompt engineering.

This repo is a safe-to-edit enhanced starter derived from your original workspace. It includes a structured prompt store area, a simple backend, and a conservative migration helper to import prompts.

Current product direction:
- [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) explains the business problem, target users, and phased roadmap.
- [docs/NEXT_PHASE_PLAN.md](docs/NEXT_PHASE_PLAN.md) defines the next execution milestone (UI screens, data/AI jobs, and automation).
- [docs/UI.md](docs/UI.md) shows how to run and understand the Streamlit dashboard.
- [docs/PIPELINE.md](docs/PIPELINE.md) explains dataset ingestion, evaluation automation, and release readiness checks.
- [workflows/README.md](workflows/README.md) starts the first operational workflow: prompt approval.

Diagram:

- Request flow (text + mermaid): [workflows/request_flow.md](workflows/request_flow.md)
- Rendered diagram: ![request flow](workflows/request_flow.svg)

Implemented workflow pieces:
- JSON-backed prompt approval store in `data/prompt_approvals.json`
- Workflow API endpoints in `backend/app.py`
- Metadata schema in `workflows/prompt_metadata_schema.json`

Next steps:
- Run the migration script to import prompts from the original `llm-prompt-repository`.
- Add CI, linting, and tests.
- Expand the prompt approval workflow into validation, testing, and publishing automation.

Development checks:
```bash
python3 -m unittest discover -s tests -v
python3 -m coverage run -m unittest discover -s tests
python3 -m coverage report -m
python3 -m ruff check backend tests
python3 -m mypy backend
```

Secrets and configuration management:
- copy [.env.example](.env.example) to `.env` for local development
- keep secrets like API keys out of source control
- use environment variables to set runtime values such as host, port, and data directory
- `backend/settings.py` loads `.env` first, then falls back to safe defaults

Common environment variables:
- `INTELLECTIVE_AI_HOST`
- `INTELLECTIVE_AI_PORT`
- `INTELLECTIVE_AI_DATA_DIR`
- future integration secrets such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `SENTRY_DSN`

Continuous integration:
- GitHub Actions runs linting, type checks, the same test suite, and coverage checks on pull requests and pushes to `main`.

Containerization and deployment:
- [Dockerfile](Dockerfile) packages the app and its workflow files into one repeatable image
- [docker-compose.yml](docker-compose.yml) runs the app locally with a persistent `data/` volume
- [DEPLOYMENT.md](DEPLOYMENT.md) shows the Docker and Compose commands
- Docker is useful because it makes the runtime reproducible on a laptop, in CI, or in the cloud

Logging, monitoring, and model adapter:
- structured JSON logs are emitted from the backend
- `GET /metrics` exposes Prometheus-style counters for requests and adapter calls
- `POST /generate` uses a small model-adapter abstraction so the app can swap providers later
- the default adapter is local and deterministic, which keeps the repo usable without API keys
- this is the core idea behind adapter abstraction: one app interface, many possible model providers underneath

Quick start with Docker:
```bash
docker build -t intellective-ai .
docker run --rm -p 8000:8000 -e INTELLECTIVE_AI_HOST=0.0.0.0 -e INTELLECTIVE_AI_PORT=8000 intellective-ai
```

Quick start with Compose:
```bash
docker compose up --build
```

Files in this scaffold:
- `requirements.txt`
- `backend/` (starter app)
- `prompts/` (target for migrated prompts)
- `migrate_prompts.py` (helper to copy prompts)
- `workflows/` (workflow definitions)
- `PRODUCT_BRIEF.md` (scope and roadmap)

To run locally (create & activate venv first):

```bash
python -m pip install -r requirements.txt
python backend/app.py
```
