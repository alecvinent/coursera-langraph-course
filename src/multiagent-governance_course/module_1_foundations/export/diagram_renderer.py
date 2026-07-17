from __future__ import annotations

import fitz
from log import logger
from module_1_foundations.scenarios.base import InteractionType, Scenario

NODE_W = 150
NODE_H = 55
MARGIN_X = 40
MARGIN_Y = 40
COL_GAP = 40
ROW_GAP = 20
ARROW_LEN = 30
FONT_SIZE = 9
FONT = "helv"


def _draw_rounded_rect(page, x, y, w, h, fill, stroke):
    # Simple rectangle (pymupdf version compatibility)
    page.draw_rect((x, y, x + w, y + h), color=stroke, fill=fill, width=0.5)


def _draw_arrow(page, x1, y1, x2, y2, label=""):
    page.draw_line((x1, y1), (x2, y2), color=(0.3, 0.3, 0.3), width=0.5)
    # arrowhead
    dx, dy = x2 - x1, y2 - y1
    length = (dx * dx + dy * dy) ** 0.5
    if length > 0:
        ux, uy = dx / length, dy / length
        ah_size = 6
        px, py = x2 - ux * ah_size, y2 - uy * ah_size
        perp_x, perp_y = -uy * ah_size * 0.4, ux * ah_size * 0.4
        page.draw_line((x2, y2), (px + perp_x, py + perp_y), color=(0.3, 0.3, 0.3), width=0.5)
        page.draw_line((x2, y2), (px - perp_x, py - perp_y), color=(0.3, 0.3, 0.3), width=0.5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 4
        page.insert_textbox((mx - 60, my - 8, mx + 60, my + 8), label, fontname=FONT, fontsize=FONT_SIZE - 1, color=(0.3, 0.3, 0.3), align=1)


def render_interaction_diagram(doc: fitz.Document, page_num: int, scenario: Scenario) -> None:
    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height
    agents = scenario.agents
    n = len(agents)
    if n == 0:
        return

    total_w = n * NODE_W + (n - 1) * COL_GAP
    start_x = (pw - total_w) / 2
    node_centers = {}

    for i, agent in enumerate(agents):
        x = start_x + i * (NODE_W + COL_GAP)
        y = ph / 2 - NODE_H / 2
        _draw_rounded_rect(page, x, y, NODE_W, NODE_H, fill=(0.9, 0.93, 0.97), stroke=(0.3, 0.5, 0.7))
        page.insert_textbox((x + 5, y + 4, x + NODE_W - 5, y + NODE_H / 2), agent.name, fontname=FONT, fontsize=FONT_SIZE, color=(0.1, 0.1, 0.1))
        page.insert_textbox((x + 5, y + NODE_H / 2 + 2, x + NODE_W - 5, y + NODE_H - 4), f"({agent.id})", fontname=FONT, fontsize=FONT_SIZE - 1, color=(0.5, 0.5, 0.5))
        node_centers[agent.id] = (x + NODE_W / 2, y + NODE_H / 2)

    for ix in scenario.interactions:
        src = node_centers.get(ix.source)
        tgt = node_centers.get(ix.target)
        if src and tgt:
            _draw_arrow(page, src[0] + NODE_W / 2, src[1], tgt[0] - NODE_W / 2, tgt[1], label=ix.label)


def render_capability_cycle_diagram(doc: fitz.Document, page_num: int, scenario: Scenario, agent_id: str) -> None:
    agent = None
    for a in scenario.agents:
        if a.id == agent_id:
            agent = a
            break
    if agent is None:
        raise ValueError(f"Agent '{agent_id}' not found in scenario '{scenario.id}'")

    page = doc[page_num]
    pw, ph = page.rect.width, page.rect.height

    subgraph_data = [
        ("Perception", ["Receive environmental input", "Detect relevant changes"], (0.95, 0.98, 1.0)),
        ("Reasoning", ["Evaluate alternatives", "Select best action"], (0.98, 0.95, 1.0)),
        ("Action", ["Execute via tools", "Monitor outcome"], (0.95, 1.0, 0.95)),
    ]

    col_w = NODE_W + 40
    total_w = 3 * col_w
    start_x = (pw - total_w) / 2
    start_y = ph / 2 - 80

    for col_idx, (title, nodes, bg_color) in enumerate(subgraph_data):
        x = start_x + col_idx * col_w
        # subgraph box
        sg_h = 160
        page.draw_rect((x - 10, start_y - 20, x + NODE_W + 10, start_y + sg_h), color=(0.6, 0.6, 0.6), fill=bg_color, width=0.3)
        page.insert_textbox((x - 5, start_y - 18, x + NODE_W + 5, start_y - 2), title, fontname=FONT, fontsize=FONT_SIZE, color=(0.2, 0.2, 0.2))

        for row_idx, node_text in enumerate(nodes):
            nx = x
            ny = start_y + 10 + row_idx * (NODE_H + ROW_GAP)
            _draw_rounded_rect(page, nx, ny, NODE_W, NODE_H, fill=(1, 1, 1), stroke=(0.4, 0.4, 0.4))
            page.insert_textbox((nx + 5, ny + 5, nx + NODE_W - 5, ny + NODE_H - 5), node_text, fontname=FONT, fontsize=FONT_SIZE - 1, color=(0.1, 0.1, 0.1))

            # arrow down within subgraph
            if row_idx < len(nodes) - 1:
                ay = ny + NODE_H
                _draw_arrow(page, nx + NODE_W / 2, ay, nx + NODE_W / 2, ay + ROW_GAP - 5)

        # arrow to next subgraph
        if col_idx < 2:
            ax = x + NODE_W + 5
            ay = start_y + 10 + NODE_H / 2
            bx = ax + col_w - NODE_W - 10
            _draw_arrow(page, ax, ay, bx, ay, label="")
