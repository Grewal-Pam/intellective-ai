# Prompt Evaluation Flow Example

This example shows how the second workflow works: evaluating prompts before they are promoted.

## Scenario
A prompt author has a draft prompt and wants to know whether it performs well on a test dataset before publishing it.

## Step-by-step flow

### 1) Prompt is ready for evaluation
The prompt has already been written and has a basic approval state, but now it needs testing against examples.

The evaluation owner queues the prompt for testing with:
- prompt id
- evaluation dataset
- success metrics

State: `queued`

### 2) Evaluation runs
The evaluator runs the prompt against a test set and scores it.

State change:
- `queued` -> `running`
- `running` -> `scored`

What is being measured:
- accuracy
- relevance
- safety
- consistency

### 3) Reviewer interprets results
If the scores are good enough:
- the prompt is accepted
- it can move forward toward approval or publication

State change:
- `scored` -> `accepted`

If the scores are weak:
- the prompt is marked `needs_revision`
- the author updates the prompt
- the prompt is evaluated again

State change:
- `scored` -> `needs_revision`

### Example lifecycle summary
```text
queued -> running -> scored -> accepted
                   \-> needs_revision -> queued -> running -> scored
```

## What this workflow is trying to do
This workflow makes sure prompts are not only approved by humans, but also validated against real examples.
It helps the team:
- catch weak prompt behavior early
- compare prompt versions objectively
- reduce production risk
- prove the prompt meets success thresholds
