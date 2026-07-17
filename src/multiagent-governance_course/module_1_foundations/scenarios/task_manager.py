from .base import (
    AgentAttribute,
    AgentDef,
    InteractionDef,
    Scenario,
)


task_manager_scenario = Scenario(
    id="personal_task_manager",
    name="Personal Task Manager",
    description="""An AI personal assistant that helps manage schedules by monitoring
calendars and weather data, reasoning about conflicts, and executing actions.""",
    agents=[
        AgentDef(
            id="personal_assistant",
            name="Personal Assistant",
            description="""Monitors calendar and weather APIs, detects scheduling conflicts,
evaluates alternatives, and updates appointments. Combines reactive alert handling
with deliberative planning.""",
            attributes=[
                AgentAttribute(name="internal_state", value="partial", description="Temporary working memory during conflict resolution"),
                AgentAttribute(name="planning_horizon", value="short_term"),
                AgentAttribute(name="memory", value="short_term"),
                AgentAttribute(name="decision_logic", value="utility"),
                AgentAttribute(name="adaptability", value="medium"),
                AgentAttribute(name="sensing", value="both"),
            ],
        ),
    ],
    interactions=[],
)
