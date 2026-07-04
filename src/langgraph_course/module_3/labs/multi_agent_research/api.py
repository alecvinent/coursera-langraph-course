from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.state import (
    ResearchRequest,
    ResearchRequestStatus,
    ResearchState,
    SteeringInstruction,
)
from langgraph_course.module_3.labs.multi_agent_research.telemetry.events import (
    get_buffer,
)

app = FastAPI(title="Multi-Agent Research System", version="0.1.0")

_workflows: dict[str, ResearchState] = {}


@app.post("/research")
async def submit_research(topic: str, domain_tags: list[str] | None = None) -> dict:
    request_id = str(uuid.uuid4())
    state = ResearchState(
        request=ResearchRequest(topic=topic, domain_tags=domain_tags or [])
    )
    _workflows[request_id] = state
    logger.info("Research request created: id={} topic='{}'", request_id, topic)
    return {"request_id": request_id, "status": ResearchRequestStatus.PENDING.value}


@app.get("/research/{request_id}/findings")
async def get_findings(request_id: str) -> dict:
    state = _workflows.get(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Research request not found")
    findings = {
        role: [f.model_dump() for f in fs]
        for role, fs in state.agent_outputs.items()
    }
    return {"findings": findings}


@app.post("/research/{request_id}/steer")
async def steer_research(
    request_id: str, instruction_text: str, target_agents: list[str]
) -> dict:
    state = _workflows.get(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Research request not found")
    instruction = SteeringInstruction(
        instruction_text=instruction_text, target_agents=target_agents, applied=True
    )
    state.steering_instructions.append(instruction)
    logger.info(
        "Steering applied: id={} instruction='{}' agents={}",
        request_id,
        instruction_text,
        target_agents,
    )
    return {"request_id": request_id, "applied": True}


@app.get("/research/{request_id}/report")
async def get_report(request_id: str) -> dict:
    state = _workflows.get(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Research request not found")
    if not state.report:
        raise HTTPException(status_code=400, detail="Report not yet generated")
    return {"report": state.report.model_dump()}


@app.get("/research/{request_id}/status")
async def get_status(request_id: str) -> dict:
    state = _workflows.get(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Research request not found")
    agent_states = {
        role: agent.execution_state.value
        for role, agent in state.agent_states.items()
    }
    return {
        "request_id": request_id,
        "status": state.request.status.value,
        "agents": agent_states,
        "steering_count": len(state.steering_instructions),
        "conflict_count": len(state.conflicts),
    }


@app.post("/research/{request_id}/intervene")
async def intervene_workflow(
    request_id: str, action: str, agent_role: str | None = None
) -> dict:
    state = _workflows.get(request_id)
    if not state:
        raise HTTPException(status_code=404, detail="Research request not found")
    if action not in ("resume", "restart", "abort"):
        raise HTTPException(status_code=400, detail="Invalid action")
    logger.info(
        "Intervention: id={} action={} agent={}",
        request_id,
        action,
        agent_role or "all",
    )
    if action == "abort":
        state.request.status = ResearchRequestStatus.FAILED
        state.execution_metadata["intervention"] = "aborted"
    elif action == "restart" and agent_role:
        if agent_role in state.agent_states:
            from langgraph_course.module_3.labs.multi_agent_research.state import (
                ExecutionState,
            )

            state.agent_states[agent_role].execution_state = ExecutionState.IDLE
    return {
        "request_id": request_id,
        "status": state.request.status.value,
    }


@app.get("/telemetry")
async def get_telemetry(window: int = 100) -> dict:
    buffer = get_buffer()
    events = buffer.query(window=window)
    return {
        "events": [e.model_dump() for e in events],
        "summary": buffer.summary(window=window),
    }

import uvicorn

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
