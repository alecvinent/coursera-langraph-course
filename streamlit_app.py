import json
import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langgraph_course.agents.cafe_agent import run_agent_full as run_cafe_agent
from langgraph_course.agents.cafe.prompts import system_prompt
from langgraph_course.agents.cafe.tools import _clear
from langgraph_course.agents.weather_agent import WeatherAgent
from langgraph_course.log import logger
from langgraph_course.module_2.labs.legal_documents import LegalDocumentAgent, sample_documents
from langgraph_course.module_3.labs.multi_agent_research.graph import (
    stream_research,
)

st.set_page_config(page_title="LangGraph Agents", layout="centered")

IMAGE_URL_PATTERN = re.compile(r"https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s]*)?")

_BOOTSTRAP_LOADED = False


def _weather_cards_html(data: dict) -> str:
    daily = data.get("daily", [])
    if not daily:
        return ""
    rows = []
    for day in daily:
        rows.append(f"""<div class="col-md-4 mb-4">
<div class="card h-100 shadow-sm" style="width: 18rem;">
  <div class="card-img-top text-center pt-3 bg-light">
    <img src="{day['weather_image']}" alt="{day.get('date', '')}" style="width:80px;height:80px">
  </div>
  <div class="card-body">
    <h5 class="card-title">{day['date']}</h5>
    <h2 class="text-primary">{day['temperature']}°F</h2>
    <p class="card-text">
      H: {day['highest_temperature']}° &nbsp; L: {day['lowest_temperature']}°<br>
      <small class="text-muted">☀ {day['sunrise']} &nbsp; ☾ {day['sunset']}</small>
    </p>
    <hr>
    <div style="font-size:0.85rem">""")
        for h in day.get("hourly", []):
            rows.append(f"""<div class="d-flex justify-content-between">
        <span>{h['time'][:5]}</span>
        <span><img src="https://openweathermap.org/img/wn/{_icon_code(h['kind'])}.png" width="24"></span>
        <span>{h['temperature']}°</span>
        <span class="text-muted">{h['description']}</span>
      </div>""")
        rows.append("""</div></div></div></div>""")
    return f"""
<link href="https://cdn.jsdelivr.net/npm/mdb-ui-kit@8.1.0/css/mdb.min.css" rel="stylesheet">
<div class="row">{''.join(rows)}</div>"""


def _icon_code(kind: str) -> str:
    _map = {
        "SUNNY": "01d", "CLEAR": "01d", "PARTLY_CLOUDY": "02d",
        "CLOUDY": "03d", "VERY_CLOUDY": "04d", "FOG": "50d",
        "DRIZZLE": "50d", "LIGHT_SHOWERS": "10d", "LIGHT_RAIN": "10d",
        "HEAVY_SHOWERS": "09d", "HEAVY_RAIN": "09d",
        "LIGHT_SLEET": "13d", "LIGHT_SLEET_SHOWERS": "13d",
        "LIGHT_SNOW": "13d", "HEAVY_SNOW": "13d",
        "LIGHT_SNOW_SHOWERS": "13d", "HEAVY_SNOW_SHOWERS": "13d",
        "THUNDERY_SHOWERS": "11d", "THUNDERY_HEAVY_RAIN": "11d",
        "THUNDERY_SNOW_SHOWERS": "11d",
    }
    return _map.get(kind.upper(), "01d")


def _render_weather(data: dict) -> None:
    global _BOOTSTRAP_LOADED
    if not _BOOTSTRAP_LOADED:
        st.markdown(
            "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>",
            unsafe_allow_html=True,
        )
        _BOOTSTRAP_LOADED = True
    st.markdown(
        f"<h4 class='mb-0'>{data['location']}</h4><p class='text-muted'>{data['temperature']}°F current</p>",
        unsafe_allow_html=True,
    )
    st.markdown(_weather_cards_html(data), unsafe_allow_html=True)


def _parse_item_line(line: str) -> dict:
    line = line.lstrip("- ").strip()
    parts = line.split(":", 1)
    if len(parts) >= 2:
        name = parts[0].strip()
        rest = parts[1].strip()
        price = ""
        desc = ""
        if rest.startswith("$"):
            price = rest.split("—")[0].strip() if "—" in rest else rest
            desc = rest.split("—")[1].strip() if "—" in rest else ""
        else:
            desc = rest
        return {"name": name, "price": price, "description": desc, "tags": [], "variations": [], "image_url": ""}
    return {"name": line, "price": "", "description": "", "tags": [], "variations": [], "image_url": ""}


def _parse_item_block(text: str) -> list[dict]:
    lines = text.strip().split("\n")
    items: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line.startswith("- "):
            if current:
                items.append(current)
            current = _parse_item_line(line)
        elif current and line.strip().startswith("Image:"):
            current["image_url"] = line.replace("Image:", "").strip()
        elif current and line.strip().startswith("Tags:"):
            current["tags"] = [t.strip() for t in line.replace("Tags:", "").split(",") if t.strip()]
        elif current and line.strip().startswith("Variations:"):
            current["variations"] = [v.strip() for v in line.replace("Variations:", "").split(",") if v.strip()]
        elif current and line.strip():
            current["description"] = (current["description"] + " " + line.strip()).strip()
    if current:
        items.append(current)
    return items


def _product_img(name: str) -> str:
    key = name.lower().strip().replace(" ", "-")
    return f"https://picsum.photos/seed/{key}/400/250"


def _cafe_card_html(text: str) -> str:
    lines = text.strip().split("\n")
    if not lines:
        return ""
    first = lines[0]

    if first.startswith("Today's Menu"):
        title = "📋 Today's Menu"
        items = _parse_item_block(text)
    elif first.startswith("Today's Recommendations"):
        title = "⭐ Recommendations"
        items = _parse_item_block(text)
    elif first.startswith("Items matching"):
        title = first
        items = _parse_item_block(text)
    elif first.startswith("Added") or first.startswith("Order confirmed"):
        title = "🛒 Order Updated" if first.startswith("Added") else "✅ Order Confirmed"
        items = []
    elif first.startswith("Your Orders") or "You have no orders" in text:
        title = "📦 Your Orders"
        items = []
    elif first.startswith("Customer details saved"):
        title = "👤 Customer Info"
        items = []
    elif "Sorry" in first or "not on the menu" in text:
        title = "😕 Oops"
        items = _parse_item_block(text)
    else:
        title = "🤖 Bistro Cafe"
        items = []

    body = "\n".join(lines).strip()

    if items:
        grid_cards = ""
        for item in items:
            tags_html = "".join(f'<span class="badge bg-primary me-1">{t}</span>' for t in item["tags"])
            vars_html = ""
            if item["variations"]:
                vars_html = '<div class="mt-2"><small class="text-muted">Variations:</small><div class="d-flex flex-wrap gap-1 mt-1">' + \
                    "".join(f'<span class="badge bg-light text-dark">{v}</span>' for v in item["variations"]) + "</div></div>"
            price_tag = f'<span class="mb-0">{item["price"]}</span>' if item["price"] else ""
            desc = item["description"] or ""

            img_url = item['image_url'] or _product_img(item['name'])
            grid_cards += f"""
      <div class="col-sm-6 col-lg-4 mb-3">
        <div class="card">
          <img src="{img_url}" class="card-img-top" alt="{item['name']}" style="height:140px;object-fit:cover">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-1">
              <h5 class="card-title mb-0">{item['name']}</h5>
              {price_tag}
            </div>
            <p class="card-text">{desc}</p>
            {tags_html}
            {vars_html}
          </div>
        </div>
      </div>"""
        body_content = f"""<div class="card mb-2">
  <div class="card-header">{title}</div>
</div>
<div class="row">{grid_cards}</div>"""
    else:
        body_lines = [l for l in lines if l != first] if first else lines
        body_html = "<br>".join(l for l in body_lines if l.strip())
        body_content = f"""<div class="card mb-3">
  <div class="card-header">{title}</div>
  <div class="card-body"><p class="card-text mb-0">{body_html}</p></div>
</div>"""

    return body_content


def _render_cafe(text: str) -> None:
    global _BOOTSTRAP_LOADED
    if not _BOOTSTRAP_LOADED:
        st.markdown(
            "<link href='https://cdn.jsdelivr.net/npm/mdb-ui-kit@8.1.0/css/mdb.min.css' rel='stylesheet'>",
            unsafe_allow_html=True,
        )
        _BOOTSTRAP_LOADED = True
    st.markdown(_cafe_card_html(text), unsafe_allow_html=True)


def _render_content(content: str) -> None:
    parts = IMAGE_URL_PATTERN.split(content)
    images = IMAGE_URL_PATTERN.findall(content)

    for i, part in enumerate(parts):
        if part.strip():
            st.markdown(part)
        if i < len(images):
            st.image(images[i], width=100)


AGENT_CARDS = {
    "validate_request": ("🔍", "Validating Request"),
    "web_research": ("🌐", "Web Research"),
    "data_analysis": ("📊", "Data Analysis"),
    "trend_analysis": ("📈", "Trend Analysis"),
    "competitive_intel": ("🏢", "Competitive Intel"),
    "synthesize": ("📝", "Synthesis"),
    "needs_refinement": ("✏️", "Needs Refinement"),
}


def _render_agent_card(icon: str, label: str, findings: list | None, elapsed: str = "") -> str:
    if findings:
        lines = [f"<small>{elapsed}</small>"] if elapsed else []
        for f in findings:
            content = f.content[:150] if hasattr(f, "content") else str(f)[:150]
            conf = f.confidence if hasattr(f, "confidence") else 0
            lines.append(
                f"<div style='padding:4px 0'><span style='font-size:0.9em'>{content}</span>"
                f"<br><span style='font-size:0.75em;color:gray'>confidence: {conf:.0%}</span></div>"
            )
        body = "".join(lines)
    else:
        body = f"<div style='padding:8px 0'><span style='color:gray'>⏳ Running...</span></div>"
    return f"""
<div style="border:1px solid #ddd;border-radius:8px;padding:8px 12px;margin:6px 0">
  <strong>{icon} {label}</strong>
  {body}
</div>"""


agent_mode = st.sidebar.radio("Agent", ["☕ Cafe", "🌤 Weather", "📄 Legal Docs", "🧠 Research"], index=0)

if agent_mode == "☕ Cafe":
    title = "☕ Bistro Cafe"
    caption = "LangGraph-powered ordering assistant"
    chat_placeholder = "Ask about the menu, place an order..."
    run_agent = run_cafe_agent
    system_info = system_prompt.strip()
elif agent_mode == "🌤 Weather":
    title = "🌤 Weather Agent"
    caption = "LangGraph-powered weather assistant"
    chat_placeholder = "Ask about the weather..."
    system_info = "Weather assistant that fetches live forecasts."
    run_agent = lambda prompt, provider=None: WeatherAgent(provider=provider).run_agent(prompt)
elif agent_mode == "📄 Legal Docs":
    title = "📄 Legal Document Processor"
    caption = "Resilient document processing with error handling & compliance"
    chat_placeholder = "Paste legal document text..."
    system_info = "Processes legal documents through a multi-stage pipeline with retry/backoff, graceful degradation, and human review escalation."

    def _run_legal(prompt: str, provider: str | None = None) -> dict:
        pending = st.session_state.pop("_legal_pending", None)
        if pending:
            return LegalDocumentAgent(provider=provider).run(pending)
        if "_legal_doc_count" not in st.session_state:
            st.session_state._legal_doc_count = 0
        st.session_state._legal_doc_count += 1
        urgency_val = st.session_state.get("_legal_urgency", "standard")
        return LegalDocumentAgent(provider=provider).run({
            "document_id": "DOC-{:04d}".format(st.session_state._legal_doc_count),
            "raw_text": prompt,
            "urgency": urgency_val,
        })

    run_agent = _run_legal
else:
    title = "🧠 Multi-Agent Research"
    caption = "LangGraph-powered multi-agent market research"
    chat_placeholder = "Enter a research topic (e.g., 'EV battery market in SE Asia')..."
    system_info = (
        "Coordinates 5 specialized agents (web research, data analysis, trend analysis, "
        "competitive intelligence, synthesis) to produce comprehensive market analysis reports."
    )
    run_agent = None  # handled separately via stream_research

with st.sidebar:
    st.title(title)
    st.caption(caption)

    provider = st.selectbox(
        "LLM Provider",
        ["openrouter", "auto", "openai", "anthropic"],
        index=0,
        help="Which LLM backend to use.",
    )

    if agent_mode == "☕ Cafe":
        if st.button("🔄 New Order", type="primary", use_container_width=True):
            _clear()
            st.session_state.messages = []
            st.rerun()
        with st.expander("ℹ️ System Prompt"):
            st.text(system_info)

    elif agent_mode == "🌤 Weather":
        if st.button("🔄 New Chat", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        with st.expander("ℹ️ Info"):
            st.text("Uses the internal weather API at localhost:8000")

    elif agent_mode == "📄 Legal Docs":
        if st.button("🔄 New Document", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.session_state._legal_doc_count = 0
            st.rerun()
        urgency = st.selectbox("Urgency", ["standard", "rush"], index=0, key="_legal_urgency", help="Rush skips complex LLM processing for faster results.")

        sample_idx = st.selectbox("Sample Document", range(len(sample_documents)), format_func=lambda i: "{} — {}".format(sample_documents[i]["document_id"], sample_documents[i].get("description", "Standard document")), index=0)
        if st.button("📋 Load Sample", use_container_width=True):
            st.session_state._legal_pending = dict(sample_documents[sample_idx])
            st.session_state._legal_pending.pop("description", None)
            st.rerun()
        with st.expander("ℹ️ Info"):
            st.text("4-stage pipeline: extract → validate → process → summarize\n• Retry/backoff on API failures\n• Regex fallback when services degrade\n• Human review for unrecoverable docs")

    else:
        if st.button("🔄 New Research", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        with st.expander("ℹ️ Info"):
            st.text("5-agent system: Web Research → Data Analysis → Trend Analysis → Competitive Intel → Synthesis")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        content = msg["content"]
        if isinstance(content, list):
            for block in content:
                if block["type"] == "text":
                    st.markdown(block["text"])
                elif block["type"] == "image_url":
                    st.image(block["image_url"]["url"])
        elif msg["role"] == "assistant" and agent_mode == "☕ Cafe":
            _render_cafe(content)
        else:
            _render_content(content)

def _process_prompt(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ""
        weather_data = None
        cafe_images: list[str] = []
        research_state = None

        if agent_mode == "🧠 Research":
            with st.status("🧠 Research in progress...", expanded=True) as research_status:
                try:
                    card_placeholders = {}
                    for node_key, (icon, label) in AGENT_CARDS.items():
                        card_placeholders[node_key] = st.empty()
                        card_placeholders[node_key].markdown(
                            _render_agent_card(icon, label, None),
                            unsafe_allow_html=True,
                        )

                    for node_name, state in stream_research(
                        topic=prompt, max_execution_minutes=10
                    ):
                        if node_name in card_placeholders:
                            findings = state.agent_outputs.get(node_name, []) if node_name != "synthesize" else []
                            card_placeholders[node_name].markdown(
                                _render_agent_card(
                                    *AGENT_CARDS[node_name],
                                    findings,
                                ),
                                unsafe_allow_html=True,
                            )

                    research_state = state
                    report = state.report
                    if report:
                        sections = report.sections or []
                        response = "\n\n".join(
                            s.get("content", "") for s in sections if s.get("content")
                        ) or "Research completed — no report sections generated."
                    else:
                        response = "Research completed, but no report was generated."
                    research_status.update(label="✅ Research complete", state="complete")
                except Exception as e:
                    logger.opt(exception=True).error("Research error")
                    response = f"Research failed:\n\n```\n{e}\n```"
                    research_status.update(label="❌ Research failed", state="error")
        else:
            with st.status("Thinking…", expanded=False) as status:
                try:
                    result = run_agent(prompt, provider=provider)

                    if agent_mode == "📄 Legal Docs":
                        response = result.get("summary", "No summary generated")
                        status.update(label="Done", state="complete")
                    elif agent_mode == "🌤 Weather":
                        messages = result.get("messages", [])
                        last = messages[-1] if messages else {}
                        if hasattr(last, "content"):
                            response = last.content
                        elif isinstance(last, dict):
                            response = last.get("content", "")
                        else:
                            response = str(last)
                        for m in messages:
                            if not hasattr(m, "content"):
                                continue
                            text = str(m.content)
                            if getattr(m, "name", None) == "get_weather":
                                try:
                                    weather_data = json.loads(text)
                                except (json.JSONDecodeError, TypeError):
                                    pass
                    else:
                        messages = result.get("messages", [])
                        last = messages[-1] if messages else {}
                        if hasattr(last, "content"):
                            response = last.content
                        elif isinstance(last, dict):
                            response = last.get("content", "")
                        else:
                            response = str(last)
                        for m in messages:
                            if not hasattr(m, "content"):
                                continue
                            text = str(m.content)
                            if getattr(m, "name", None) in ("get_daily_menu", "get_recommendations", "recommend_by_preference"):
                                body = json.loads(text) if text.startswith("{") else None
                                if body:
                                    for day in body.get("daily", []):
                                        img = day.get("weather_image")
                                        if img:
                                            cafe_images.append(img)
                                else:
                                    cafe_images.extend(IMAGE_URL_PATTERN.findall(text))

                    status.update(label="Done", state="complete")
                except Exception as e:
                    logger.opt(exception=True).error("Agent error")
                    response = f"Sorry, something went wrong:\n\n```\n{e}\n```"
                    status.update(label="Error", state="error")
        if agent_mode == "📄 Legal Docs":
            st.markdown(response)
            with st.expander("📊 Processing Details"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Processing Time", "{:.1f}ms".format(result.get("total_processing_time", 0) * 1000))
                col2.metric("Outcome", result.get("compliance", {}).get("processing_outcome", "?"))
                col3.metric("Fallback Used", "Yes" if result.get("error_handling", {}).get("fallback_used") else "No")
                with st.expander("🛤️ Path Taken"):
                    st.write(result.get("paths_taken", []))
                with st.expander("⏱️ Latencies"):
                    st.json(result.get("latencies", {}))
                with st.expander("📋 Compliance Audit Trail"):
                    st.json(result.get("compliance", {}).get("audit_trail", []))
                with st.expander("⚠️ Error Logs"):
                    st.json(result.get("error_handling", {}).get("error_logs", []))
        elif agent_mode == "☕ Cafe":
            _render_cafe(response)
            for url in cafe_images:
                st.image(url, width=100)
        elif agent_mode == "🧠 Research":
            st.markdown(response)
            if research_state:
                with st.expander("📊 Per-Agent Contributions"):
                    for role, findings in research_state.agent_outputs.items():
                        if findings:
                            with st.container():
                                st.markdown(f"**{role.replace('_', ' ').title()}** ({len(findings)} findings)")
                                for f in findings:
                                    st.markdown(f"- {f.content[:200]}")
                                    st.caption(f"Confidence: {f.confidence:.0%} | Source: {f.source}")

                with st.expander("⚡ Conflicts Detected"):
                    if research_state.conflicts:
                        for c in research_state.conflicts:
                            st.markdown(f"- **{c.description}**")
                            st.caption(f"Status: {c.resolution_status.value}")
                    else:
                        st.markdown("No conflicts detected.")

                with st.expander("🏷️ Provenance Trace"):
                    if research_state.report and research_state.report.provenance_trace:
                        st.json(research_state.report.provenance_trace)
                    else:
                        st.markdown("Provenance trace not available.")

                total_findings = sum(len(v) for v in research_state.agent_outputs.values())
                col1, col2 = st.columns(2)
                col1.metric("Agents Activated", len(research_state.agent_outputs))
                col2.metric("Total Findings", total_findings)
                if research_state.report:
                    st.caption(f"Report generated: {research_state.report.generated_at.strftime('%H:%M:%S UTC')}")
        else:
            _render_content(response)
        if weather_data:
            _render_weather(weather_data)

    st.session_state.messages.append({"role": "assistant", "content": response})


# Handle sample document load before chat_input
if agent_mode == "📄 Legal Docs" and "_legal_pending" in st.session_state:
    sample = st.session_state["_legal_pending"]
    _process_prompt(sample.get("raw_text", ""))

if prompt := st.chat_input(chat_placeholder):
    _process_prompt(prompt)
