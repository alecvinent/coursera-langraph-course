from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from log import logger

from module_1_foundations.analysis.tradeoffs import generate_tradeoff_analysis
from module_1_foundations.classification.graph import classify_agent
from module_1_foundations.export.submission import compile_submission, generate_pdf
from module_1_foundations.interaction_map.mapper import (
    generate_capability_cycle,
    generate_interaction_map,
)
from module_1_foundations.scenarios.task_manager import task_manager_scenario
from module_1_foundations.scenarios.traffic import traffic_scenario

SCENARIOS = {
    "Traffic Control System": traffic_scenario,
    "Personal Task Manager": task_manager_scenario,
}

st.set_page_config(page_title="Agent Ecosystem Mapping", layout="wide")
st.title("Agent Ecosystem Mapping")
st.markdown("Classify agents, map interactions, analyze trade-offs, and export your submission.")

if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.scenario = None
    st.session_state.classifications = []
    st.session_state.interaction_map = ""
    st.session_state.capability_cycle = ""
    st.session_state.tradeoff_analysis = ""
    st.session_state.submission_md = ""

step = st.session_state.step

st.sidebar.header("Workflow")
st.sidebar.progress((step - 1) / 4)
st.sidebar.write(f"Step {step} of 4")
steps_labels = ["1. Select Scenario", "2. Classify Agents", "3. View Analysis", "4. Export"]
for i, label in enumerate(steps_labels, 1):
    icon = "✅" if step > i else "⬜" if step == i else "⬜"
    st.sidebar.write(f"{icon} {label}")

if step == 1:
    st.header("Step 1: Select a Scenario")
    scenario_name = st.selectbox("Choose a predefined scenario:", list(SCENARIOS.keys()))
    if st.button("Next: Classify Agents"):
        st.session_state.scenario = SCENARIOS[scenario_name]
        st.session_state.step = 2
        st.rerun()

elif step == 2:
    st.header("Step 2: Classify Agents")
    scenario = st.session_state.scenario
    st.write(f"**Scenario**: {scenario.name}")
    st.write(scenario.description)

    if st.button("Run Classification"):
        classifications = []
        progress_bar = st.progress(0)
        for i, agent in enumerate(scenario.agents):
            try:
                result = classify_agent(agent.description, [a.model_dump() for a in agent.attributes])
                result["agent_id"] = agent.id
                classifications.append(result)
            except Exception as exc:
                logger.error(f"Classification failed for {agent.id}: {exc}")
                classifications.append({
                    "agent_id": agent.id,
                    "agent_type": "error",
                    "justification": f"Classification failed: {exc}",
                })
            progress_bar.progress((i + 1) / len(scenario.agents))
        st.session_state.classifications = classifications
        st.rerun()

    if st.session_state.classifications:
        st.subheader("Classification Results")
        data = []
        for agent in scenario.agents:
            cl = next((c for c in st.session_state.classifications if c.get("agent_id") == agent.id), {})
            data.append({
                "Agent": agent.name,
                "Type": cl.get("agent_type", "").capitalize(),
                "Method": cl.get("method", "rule_based"),
                "Justification": cl.get("justification", ""),
            })
        st.table(data)
        if st.button("Next: View Analysis"):
            st.session_state.step = 3
            st.rerun()

elif step == 3:
    st.header("Step 3: Analysis")
    scenario = st.session_state.scenario
    classifications = st.session_state.classifications

    tab1, tab2, tab3 = st.tabs(["Interaction Map", "Trade-off Analysis", "Capability Cycle"])

    with tab1:
        st.subheader("Agent Interaction Diagram")
        if not st.session_state.interaction_map:
            st.session_state.interaction_map = generate_interaction_map(scenario)
        st.code(st.session_state.interaction_map, language="mermaid")
        st.markdown("```mermaid\n" + st.session_state.interaction_map + "\n```")

    with tab2:
        st.subheader("Trade-off Analysis")
        if not st.session_state.tradeoff_analysis:
            st.session_state.tradeoff_analysis = generate_tradeoff_analysis(scenario)
        st.markdown(st.session_state.tradeoff_analysis)

    with tab3:
        st.subheader("Capability Cycle")
        if not st.session_state.capability_cycle:
            st.session_state.capability_cycle = generate_capability_cycle(scenario, scenario.agents[0].id)
        st.code(st.session_state.capability_cycle, language="mermaid")
        st.markdown("```mermaid\n" + st.session_state.capability_cycle + "\n```")

    if st.button("Next: Export Submission"):
        st.session_state.step = 4
        st.rerun()

elif step == 4:
    st.header("Step 4: Export Submission")
    scenario = st.session_state.scenario

    if not st.session_state.submission_md:
        st.session_state.submission_md = compile_submission(
            scenario=scenario,
            classifications=st.session_state.classifications,
            interaction_map=st.session_state.interaction_map,
            tradeoff_analysis=st.session_state.tradeoff_analysis,
            capability_cycle=st.session_state.capability_cycle,
        )

    md_content = st.session_state.submission_md
    st.download_button(
        label="Download Markdown (.md)",
        data=md_content,
        file_name="agent_ecosystem_mapping_submission.md",
        mime="text/markdown",
    )

    if st.button("Generate PDF"):
        pdf_path = os.path.join(tempfile.gettempdir(), f"submission_{os.urandom(4).hex()}.pdf")
        agent_id = scenario.agents[0].id if scenario.agents else None
        pdf_path = generate_pdf(md_content, pdf_path, scenario=scenario, agent_id=agent_id)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f,
                file_name="agent_ecosystem_mapping_submission.pdf",
                mime="application/pdf",
            )

    with st.expander("Preview Submission"):
        st.markdown(md_content)

    if st.button("Start Over"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
