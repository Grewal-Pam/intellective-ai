# Prompt Approval Flow Example

This example shows how a prompt moves through the approval workflow in `intellective-ai`.

## Scenario
A prompt author wants to add a customer-support reply prompt that helps answer order-status questions.

## Step-by-step flow

### 1) Draft is created
The prompt author writes a new prompt with metadata:
- name: `Support Reply`
- content: `Draft a helpful reply`
- use case: `customer support`
- expected outcome: `clear response`
- test examples: a customer asking, `Where is my order?`

At this stage, the prompt state is `draft`.

### 2) Submitted for review
The prompt author submits the prompt for review.

State change:
- `draft` -> `in_review`

Why:
- the prompt is ready for a reviewer to check quality, safety, and usefulness.

### 3) Reviewer checks the prompt
The prompt reviewer evaluates:
- clarity
- safety
- business value
- test coverage

Two outcomes are possible:
- **Approved** if the prompt is ready to ship
- **Rejected** if improvements are needed

### 4A) Approved path
If the reviewer approves the prompt:
- state change: `in_review` -> `approved`
- the product owner can publish it
- publishing sets the prompt to `published`
- the prompt receives a version tag, such as `1.0.0`

### 4B) Rejected path
If the reviewer rejects the prompt:
- state change: `in_review` -> `rejected`
- the reviewer leaves notes, such as `Needs stronger guardrails`
- the author revises the prompt
- state change: `rejected` -> `draft`
- the prompt is resubmitted for review

## Example lifecycle summary
```text
draft -> in_review -> approved -> published
           \-> rejected -> draft -> in_review -> approved -> published
```

## What this workflow is trying to do
This workflow makes prompt publishing controlled and repeatable.
It helps the team:
- keep prompt quality high
- capture review feedback
- prevent unsafe or incomplete prompts from being published
- retain an audit trail of prompt changes
