# Next Phase Plan: UI + Data/AI Pipeline + Automation

This plan answers: what we build next, what runs automatically, and what makes this interview-ready.

## 1) UI Scope (first production-facing UI)

Build a lightweight operator dashboard with these screens:

1. Prompt Registry
- list prompts with state (`draft`, `in_review`, `approved`, `published`)
- filter by tag, owner, and version
- open prompt details and history

2. Prompt Review Queue
- pending reviews
- approve/reject with notes
- see audit trail

3. Evaluation Runs
- create evaluation run from dataset
- track run status (`queued`, `running`, `scored`, `accepted`, `needs_revision`)
- compare scorecards across versions

4. Release Gate
- release checklist status
- block release until mandatory checks pass
- release with version tag

5. Runtime Monitor
- request counters and latency from `/metrics`
- adapter/provider usage
- failure panel (last errors)

## 2) Data and AI Pipeline Jobs

Define automated jobs (cron or worker queue):

1. Dataset Ingestion Job
- input: JSON/CSV test cases
- output: normalized evaluation dataset files
- validation: schema checks + duplicates check

2. Evaluation Runner Job
- picks queued evaluations
- runs prompt + context over dataset
- stores score summary and per-case notes

3. Release Guard Job
- verifies: approved prompt + accepted evaluation + checklist complete
- blocks publish on missing evidence

4. Metrics Rollup Job
- aggregates daily latency, error rate, and provider usage
- prepares trend data for dashboard

## 3) Automation Behavior (what runs by itself)

Automated path:
- new evaluation created -> queued
- runner consumes queue -> runs and scores
- release guard checks conditions continuously
- once checks pass, release endpoint allows publish

Human-in-the-loop controls:
- reviewer decision (approve/reject)
- product owner final publish sign-off

## 4) Data model to support this

Minimum entities:
- `Prompt` (id, name, content, metadata, state, version)
- `Evaluation` (prompt_id, dataset_id, status, scores)
- `Dataset` (name, cases, schema_version)
- `ReleaseChecklist` (items, completion state, owner)
- `RunMetrics` (latency, errors, provider, volume)

## 5) Why this is job/interview ready

You can clearly explain:
- product problem: prompt quality/governance in production
- system design: workflow engine + adapter + eval pipeline + observability
- reliability: CI, typing, tests, coverage, release gating
- AI relevance: model abstraction, measurable prompt quality, MCP path

## 6) Build order (recommended)

Week 1:
- UI skeleton for Prompt Registry + Review Queue
- connect existing approval endpoints

Week 2:
- Evaluation Runner job + status updates
- UI Evaluation Runs page

Week 3:
- Release Gate page + guard job
- provider config panel for adapter switching

Week 4:
- metrics dashboard widgets + docs + demo script

## 8) Current status

- Streamlit dashboard scaffold exists and is connected to the backend APIs
- pipeline dataset store exists
- evaluation runner worker exists
- release readiness endpoint exists


## 7) Definition of Done for next milestone

- UI supports create/review/evaluate/release end-to-end
- at least one automated evaluation job runs from queue
- release is blocked when required checks fail
- dashboard shows latency/error/provider usage
- demo scenario can be run in under 10 minutes
