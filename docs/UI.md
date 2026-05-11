# UI Dashboard

The first UI for `intellective-ai` is a Streamlit dashboard that sits on top of the existing backend APIs.

## Screens
- Prompt Registry: browse prompts, inspect metadata, create new prompts
- Review Queue: submit, approve, reject, and publish prompts
- Evaluation Runs: create and run evaluations, inspect scores
- Release Gate: view release-readiness status
- Runtime Monitor: read `/metrics` output

## Run locally

```bash
streamlit run streamlit_app.py
```

By default, the dashboard talks to the backend at:

```text
http://127.0.0.1:8000
```

If your backend runs elsewhere, change the base URL in the sidebar.

## Why Streamlit first
- fast to build
- good for internal operator dashboards
- works well with the existing Python backend and API-first architecture
