# Prompt Approval API Example

This example shows how to use the approval workflow through the API.

## 1) Create a draft prompt
```bash
curl -sS -X POST http://127.0.0.1:8000/prompts \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Support Reply",
    "content": "Draft a helpful reply",
    "use_case": "customer support",
    "expected_outcome": "clear response",
    "test_examples": [
      {
        "input": "Where is my order?",
        "expected": "polite status update"
      }
    ],
    "actor": "prompt_author"
  }'
```

The response returns a prompt ID and the prompt starts in `draft`.

## 2) Submit for review
```bash
curl -sS -X POST http://127.0.0.1:8000/prompts/{id}/submit \
  -H 'Content-Type: application/json' \
  -d '{"actor":"prompt_author"}'
```

State changes from `draft` to `in_review`.

## 3) Review the prompt
### Approve it
```bash
curl -sS -X POST http://127.0.0.1:8000/prompts/{id}/review \
  -H 'Content-Type: application/json' \
  -d '{"actor":"prompt_reviewer","decision":"approved","note":"Looks good"}'
```

### Or reject it
```bash
curl -sS -X POST http://127.0.0.1:8000/prompts/{id}/review \
  -H 'Content-Type: application/json' \
  -d '{"actor":"prompt_reviewer","decision":"rejected","note":"Needs stronger guardrails"}'
```

## 4) Publish after approval
```bash
curl -sS -X POST http://127.0.0.1:8000/prompts/{id}/publish \
  -H 'Content-Type: application/json' \
  -d '{"actor":"product_owner","version_tag":"1.0.0"}'
```

Final state becomes `published`.

## What this API workflow is doing
- keeps prompts from being published without review
- makes prompt changes traceable
- supports approval and rejection paths
- allows a published prompt to be versioned
