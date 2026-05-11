# Prompt Release Checklist Flow Example

This example shows the third workflow: the final release checklist before a prompt is fully released for production use.

## Scenario
A prompt has already been approved and evaluated. Before it is released, the team wants one final checklist to confirm that everything is ready.

## Who Uses This Workflow
- the release owner who verifies checklist items
- the product owner who gives release signoff
- the prompt reviewer who confirms quality evidence exists
- the prompt author who may fix anything that blocks release

## Step-by-step flow

### 1) Checklist begins
The release owner starts the checklist for a prompt that already has:
- approval records
- evaluation results
- version tags
- release notes

State: `checklist_pending` -> `checklist_in_progress`

### 2) Final checks are verified
The release owner checks:
- approval is complete
- evaluation passed
- metadata is complete
- version is tagged
- rollback plan is documented

If everything is ready:
- state becomes `ready_for_release`

If something is missing:
- state becomes `blocked`
- the team fixes the issue and restarts the checklist

### 3) Release is approved
When the checklist passes, the product owner signs off and the prompt is released.

State change:
- `ready_for_release` -> `released`

## Example lifecycle summary
```text
checklist_pending -> checklist_in_progress -> ready_for_release -> released
                               \-> blocked
```

## Why this workflow matters
This workflow exists to prove that the prompt is safe to release after approval and evaluation.
It helps the team:
- reduce release mistakes
- keep release decisions auditable
- make sure approval and evaluation actually lead to a safe production release
- create a clear final gate before users depend on the prompt
