# Deployment Notes

## What Docker Is Doing Here
Docker packages the app, its Python dependencies, and its workflow files into one repeatable image. That means the same app can run on your laptop, in CI, or in a cloud server without changing the code.

## Local Run
```bash
docker build -t intellective-ai .
docker run --rm -p 8000:8000 -e INTELLECTIVE_AI_HOST=0.0.0.0 -e INTELLECTIVE_AI_PORT=8000 intellective-ai
```

## Compose Run
```bash
docker compose up --build
```

## What Gets Exposed
- port `8000` for the API
- the `data/` directory for prompt and evaluation state

## Why This Is Useful
- one reproducible runtime for the repo
- easy local development with data persistence
- a simple path toward cloud deployment later
