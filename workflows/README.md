# Workflows

This folder defines the operating workflows for `intellective-ai`.

## First Workflow: Prompt Approval

The first workflow is the prompt approval lifecycle. It ensures prompts move through a controlled process before they are published.

## Who Can Use It
- prompt authors who create or edit prompts
- prompt reviewers who validate quality and safety
- product owners who decide what gets published
- admins who need auditability and governance

## How It Is Used
1. A prompt author creates a draft prompt with metadata and test examples.
2. The author submits it for review.
3. A reviewer approves it or sends it back for revision.
4. After approval, a product owner publishes it with a version tag.
5. The prompt stays auditable in the JSON store and can be retrieved through the API.

## Why the End Goal Is Justified
This workflow is justified because it gives `intellective-ai` a controlled release process for prompts. Without it, prompt work would be scattered, unreviewed, and hard to trust in production. The end goal is to make prompt creation reproducible, reviewable, and safe enough to use in real GenAI systems.

## Flow Diagram
```text
draft
	|
	v
in_review -----> rejected -----> draft
	|
	v
approved
	|
	v
published
```

## Example Flow
If you want to see the workflow in action with a real scenario, read:
- [example flow](examples/prompt_approval_flow_example.md)

If you want to try the workflow through the API, see:
- [API curl example](examples/prompt_approval_api_example.md)

## Second Workflow: Prompt Evaluation
The second workflow evaluates prompt quality on a test dataset before a prompt is considered production-ready.

### Who Can Use It
- evaluation owners who run prompt tests
- prompt reviewers who interpret scores
- prompt authors who want to improve prompts before publishing
- product owners who want evidence before release

### How It Is Used
1. A prompt is queued for evaluation with a dataset and success metrics.
2. The evaluation owner runs the prompt against test cases.
3. The evaluation is scored on quality, safety, and consistency.
4. If scores are good, the prompt is accepted.
5. If scores are weak, the prompt is marked for revision and sent back.

### Why the End Goal Is Justified
This workflow is justified because prompt approval alone is not enough. A prompt can look good to a human reviewer but still fail on real examples. Evaluation adds measurable proof that the prompt performs well enough for production use.

Read the example:
- [evaluation flow example](examples/prompt_evaluation_flow_example.md)

Read the spec:
- [prompt_evaluation.yaml](prompt_evaluation.yaml)

Why this workflow matters:
- it tests prompt behavior against examples instead of relying only on human judgment
- it helps compare prompt versions consistently
- it supports a safer path from draft to publish

## Third Workflow: Prompt Release Checklist
The third workflow is the final release gate. It makes sure a prompt is approved, evaluated, versioned, and ready before it is released to production use.

### Who Can Use It
- release owners who verify release readiness
- product owners who approve the final release
- prompt reviewers who confirm the evidence exists
- prompt authors who fix blocking issues before release

### How It Is Used
1. A prompt that has already passed approval and evaluation enters the checklist.
2. The release owner verifies the checklist items.
3. If everything is complete, the prompt becomes ready for release.
4. The product owner signs off and the prompt is released.
5. If anything is missing, the checklist is blocked until the issue is fixed.

### Why the End Goal Is Justified
This workflow is justified because approval and evaluation are strong signals, but they are not the same as a controlled release. The final checklist makes sure the prompt is truly production-ready, traceable, and safe to depend on.

Read the example:
- [release checklist example](examples/prompt_release_checklist_flow_example.md)

Read the spec:
- [prompt_release_checklist.yaml](prompt_release_checklist.yaml)

Why this workflow matters:
- it provides a final release gate after evaluation
- it keeps release ownership explicit
- it creates a clean handoff from prompt quality work to production use

### States
- `draft`
- `in_review`
- `approved`
- `rejected`
- `published`

### Purpose
- improve quality and consistency
- reduce unsafe or low-value prompt releases
- keep an audit trail for prompt changes

### Primary Roles
- `prompt_author`
- `prompt_reviewer`
- `product_owner`
- `admin`

### Workflow Spec
- [prompt_approval.yaml](prompt_approval.yaml)

### API Support
The backend exposes a lightweight approval API:
- `GET /workflow/prompt-approval`
- `GET /prompts`
- `POST /prompts`
- `POST /prompts/{id}/submit`
- `POST /prompts/{id}/review`
- `POST /prompts/{id}/revise`
- `POST /prompts/{id}/publish`

### Metadata Schema
- [prompt_metadata_schema.json](prompt_metadata_schema.json)
