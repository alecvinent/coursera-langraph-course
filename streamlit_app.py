import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langgraph_course.agents.cafe_agent import run_agent
from langgraph_course.agents.cafe.prompts import system_prompt
from langgraph_course.agents.cafe.tools import _clear
from langgraph_course.log import logger

st.set_page_config(page_title="Bistro Cafe Agent", page_icon="☕", layout="centered")

with st.sidebar:
    st.title("☕ Bistro Cafe")
    st.caption("LangGraph-powered ordering assistant")

    provider = st.selectbox(
        "LLM Provider",
        ["openrouter", "auto", "openai", "anthropic"],
        index=0,
        help="Which LLM backend to use.",
    )

    if st.button("🔄 New Order", type="primary", use_container_width=True):
        _clear()
        st.session_state.messages = []
        st.rerun()

    with st.expander("ℹ️ System Prompt"):
        st.text(system_prompt.strip())

if "messages" not in st.session_state:
    st.session_state.messages = [

    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about the menu, place an order..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Thinking…", expanded=False) as status:
            try:
                response = run_agent(prompt, provider=provider)
                status.update(label="Done", state="complete")
            except Exception as e:
                logger.opt(exception=True).error("Agent error")
                response = f"Sorry, something went wrong:\n\n```\n{e}\n```"
                status.update(label="Error", state="error")
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
