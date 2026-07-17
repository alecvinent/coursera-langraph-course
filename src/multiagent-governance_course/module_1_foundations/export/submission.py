from __future__ import annotations

import re
from pathlib import Path

import fitz
import markdown
from log import logger

from module_1_foundations.export.diagram_renderer import (
    render_capability_cycle_diagram,
    render_interaction_diagram,
)
from module_1_foundations.scenarios.base import Scenario


def _sanitize_for_pdf(text: str) -> str:
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # PyMuPDF insert_htmlbox chokes on <pre> tags when combined with other
    # elements like tables. Mermaid diagrams need JS anyway, so replace
    # <pre> blocks with a plain note.
    text = re.sub(
        r'<pre[^>]*>.*?</pre>',
        '<p><em>[Mermaid diagram omitted from PDF — see Markdown download]</em></p>',
        text,
        flags=re.DOTALL,
    )
    return text


def _classifications_table(scenario: Scenario, classifications: list[dict]) -> str:
    rows = ["| Agent | Type | Justification |", "|-------|------|--------------|"]
    for agent in scenario.agents:
        cl = next((c for c in classifications if c.get("agent_id", "") == agent.id), {})
        at = cl.get("agent_type", "unknown")
        jf = cl.get("justification", "").replace("|", "/")
        rows.append(f"| {agent.name} | {at} | {jf} |")
    return "\n".join(rows)


SUBMISSION_TEMPLATE = """# Agent Ecosystem Mapping - Submission

**Course**: LangGraph Framework
**Module**: Module 1 - Foundations
**Date**: {date}
**Scenario**: {scenario_name}

---

## Section 1: Agent Classification

{classification_table}

---

## Section 2: Agent Interaction Diagram

```mermaid
{interaction_map}
```

---

## Section 3: Trade-off Analysis

{tradeoff_analysis}

---

## Section 4: Capability Cycle

```mermaid
{capability_cycle}
```

---

## Section 5: Reflection

This exercise demonstrated how agent type selection directly impacts system architecture. Reactive agents (e.g., the Traffic Sensor) excel at speed and resilience with minimal overhead, while deliberative agents (e.g., the Route Planner) provide better accuracy through world modeling at the cost of latency. Hybrid agents offer the best balance but introduce coordination complexity. The perception-reasoning-action cycle (Activity 2) made clear how even a single autonomous agent requires structured input processing, alternative evaluation, and tool-based execution to function effectively. Overall, the trade-off analysis reinforced that there is no universal best agent type — the right choice depends on the system's priorities: speed, accuracy, resilience, or adaptability.
"""


def compile_submission(
    scenario: Scenario,
    classifications: list[dict],
    interaction_map: str,
    tradeoff_analysis: str,
    capability_cycle: str,
) -> str:
    from datetime import date

    return SUBMISSION_TEMPLATE.format(
        date=date.today().isoformat(),
        scenario_name=scenario.name,
        classification_table=_classifications_table(scenario, classifications),
        interaction_map=interaction_map,
        tradeoff_analysis=tradeoff_analysis,
        capability_cycle=capability_cycle,
    )


def _markdown_to_html(md_text: str) -> str:
    html_body = markdown.markdown(md_text, extensions=["extra", "codehilite"])
    html_body = _sanitize_for_pdf(html_body)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: Arial, sans-serif; font-size: 11pt; margin: 20px; }}
h1 {{ font-size: 18pt; color: #1a1a2e; }}
h2 {{ font-size: 14pt; color: #16213e; }}
h3 {{ font-size: 12pt; color: #0f3460; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ padding: 6px 10px; text-align: left; }}
td {{ border: 1px solid #ccc; }}
th {{ border: 1px solid #ccc; }}
th {{ background-color: #f0f0f0; }}
code {{ background-color: #f4f4f4; padding: 1px 4px; font-size: 10pt; }}
pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""


def generate_pdf(
    markdown_content: str,
    output_path: str,
    scenario: Scenario | None = None,
    agent_id: str | None = None,
) -> str:
    html = _markdown_to_html(markdown_content)
    doc = fitz.Document()
    page = doc.new_page()
    rect = page.rect
    rect.x1 -= 20
    rect.y1 -= 20
    rect.x0 += 20
    rect.y0 += 20
    page.insert_htmlbox(rect, html, scale_low=0.5)

    if scenario:
        page_num = len(doc)
        doc.new_page()
        page_title = f"Interaction Diagram: {scenario.name}"
        p = doc[page_num]
        p.insert_textbox((20, 10, p.rect.width - 20, 30), page_title, fontsize=12, color=(0.1, 0.1, 0.1))
        render_interaction_diagram(doc, page_num, scenario)

        if agent_id:
            cap_page = len(doc)
            doc.new_page()
            p2 = doc[cap_page]
            cap_title = f"Capability Cycle: {agent_id}"
            p2.insert_textbox((20, 10, p2.rect.width - 20, 30), cap_title, fontsize=12, color=(0.1, 0.1, 0.1))
            render_capability_cycle_diagram(doc, cap_page, scenario, agent_id)

    doc.save(output_path)
    doc.close()
    logger.info(f"PDF generated: {output_path}")
    return str(Path(output_path).resolve())
