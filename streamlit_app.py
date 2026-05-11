from __future__ import annotations

import json

import streamlit as st

from ui_helpers import (
    DEFAULT_BASE_URL,
    create_evaluation,
    create_prompt,
    get_evaluations,
    get_metrics,
    get_prompts,
    publish_prompt,
    review_prompt,
    run_evaluation,
    score_evaluation,
    submit_prompt,
)


st.set_page_config(page_title="intellective-ai", page_icon="🧠", layout="wide")

st.title("intellective-ai Dashboard")
st.caption("PromptOps, evaluation, release gating, and runtime monitoring in one place.")

base_url = st.sidebar.text_input("Backend base URL", value=DEFAULT_BASE_URL)
st.sidebar.markdown("### Navigation")
section = st.sidebar.radio(
    "Go to",
    ["Prompt Registry", "Review Queue", "Evaluation Runs", "Release Gate", "Runtime Monitor"],
)


def render_prompt_registry() -> None:
    st.subheader("Prompt Registry")
    prompts = get_prompts(base_url)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"{len(prompts)} prompt(s) found")
        for prompt in prompts:
            with st.expander(f"{prompt.get('name', 'Unnamed')} — {prompt.get('state', 'unknown')}"):
                st.json(prompt)

    with col2:
        st.markdown("### New Prompt")
        with st.form("create_prompt_form"):
            name = st.text_input("Name")
            use_case = st.text_input("Use case")
            expected_outcome = st.text_input("Expected outcome")
            content = st.text_area("Prompt content", height=160)
            submitted = st.form_submit_button("Create prompt")
            if submitted:
                result = create_prompt(
                    base_url,
                    {
                        "name": name,
                        "use_case": use_case,
                        "expected_outcome": expected_outcome,
                        "content": content,
                    },
                )
                if result.ok:
                    st.success("Prompt created")
                    st.json(result.data)
                else:
                    st.error(result.error or "failed to create prompt")


def render_review_queue() -> None:
    st.subheader("Review Queue")
    prompts = [prompt for prompt in get_prompts(base_url) if prompt.get("state") in {"draft", "in_review", "rejected", "approved"}]
    for prompt in prompts:
        with st.expander(f"{prompt.get('name', 'Unnamed')} — {prompt.get('state', 'unknown')}"):
            st.json(prompt)
            prompt_id = prompt.get("id", "")
            cols = st.columns(4)
            with cols[0]:
                if st.button("Submit", key=f"submit-{prompt_id}"):
                    result = submit_prompt(base_url, prompt_id, "reviewer")
                    st.write(result.data if result.ok else result.error)
            with cols[1]:
                if st.button("Approve", key=f"approve-{prompt_id}"):
                    result = review_prompt(base_url, prompt_id, "reviewer", "approved", "looks good")
                    st.write(result.data if result.ok else result.error)
            with cols[2]:
                if st.button("Reject", key=f"reject-{prompt_id}"):
                    result = review_prompt(base_url, prompt_id, "reviewer", "rejected", "needs changes")
                    st.write(result.data if result.ok else result.error)
            with cols[3]:
                if st.button("Publish", key=f"publish-{prompt_id}"):
                    result = publish_prompt(base_url, prompt_id, "owner", "v1.0.0")
                    st.write(result.data if result.ok else result.error)


def render_evaluation_runs() -> None:
    st.subheader("Evaluation Runs")
    evaluations = get_evaluations(base_url)
    left, right = st.columns([2, 1])

    with left:
        for evaluation in evaluations:
            with st.expander(f"Prompt {evaluation.get('prompt_id', '?')} — {evaluation.get('state', 'unknown')}"):
                st.json(evaluation)
                evaluation_id = evaluation.get("id", "")
                action_cols = st.columns(3)
                with action_cols[0]:
                    if st.button("Run", key=f"run-{evaluation_id}"):
                        result = run_evaluation(base_url, evaluation_id, "evaluator")
                        st.write(result.data if result.ok else result.error)
                with action_cols[1]:
                    if st.button("Score", key=f"score-{evaluation_id}"):
                        result = score_evaluation(base_url, evaluation_id, "evaluator", {"quality": 0.92, "safety": 0.95})
                        st.write(result.data if result.ok else result.error)

    with right:
        st.markdown("### New Evaluation")
        with st.form("create_evaluation_form"):
            prompt_id = st.text_input("Prompt ID")
            dataset = st.text_area("Evaluation dataset (JSON)", value='[{"input": "Example input", "expected": "Example output"}]')
            metrics = st.text_input("Success metrics", value="quality,safety")
            submitted = st.form_submit_button("Create evaluation")
            if submitted:
                try:
                    payload = {
                        "prompt_id": prompt_id,
                        "evaluation_dataset": json.loads(dataset),
                        "success_metrics": [item.strip() for item in metrics.split(",") if item.strip()],
                    }
                    result = create_evaluation(base_url, payload)
                    st.write(result.data if result.ok else result.error)
                except json.JSONDecodeError:
                    st.error("Dataset must be valid JSON")


def render_release_gate() -> None:
    st.subheader("Release Gate")
    st.info("This screen will enforce: approved prompt + accepted evaluation + checklist completion.")
    prompts = get_prompts(base_url)
    published = [prompt for prompt in prompts if prompt.get("state") == "published"]
    st.metric("Published prompts", len(published))
    st.metric("Total prompts", len(prompts))
    st.write("Release checklist automation is next; this panel will become the gatekeeper UI.")


def render_runtime_monitor() -> None:
    st.subheader("Runtime Monitor")
    metrics_text = get_metrics(base_url)
    st.code(metrics_text, language="text")
    st.caption("This is the first observability view for request counts, adapter calls, and latency.")


if section == "Prompt Registry":
    render_prompt_registry()
elif section == "Review Queue":
    render_review_queue()
elif section == "Evaluation Runs":
    render_evaluation_runs()
elif section == "Release Gate":
    render_release_gate()
else:
    render_runtime_monitor()
