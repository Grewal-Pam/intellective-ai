# intellective-ai

Production-ready scaffold for GenAI, RAG, and prompt engineering.

This repo is a safe-to-edit enhanced starter derived from your original workspace. It includes a structured prompt store area, a simple backend, and a conservative migration helper to import prompts.

Next steps:
- Run the migration script to import prompts from the original `llm-prompt-repository`.
- Add CI, linting, and tests.

Files in this scaffold:
- `requirements.txt`
- `backend/` (starter app)
- `prompts/` (target for migrated prompts)
- `migrate_prompts.py` (helper to copy prompts)

To run locally (create & activate venv first):

```bash
python -m pip install -r requirements.txt
python backend/app.py
```
