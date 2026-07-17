from .base import (
    AgentAttribute,
    AgentDef,
    InteractionDef,
    InteractionType,
    Scenario,
)


traffic_scenario = Scenario(
    id="traffic_control",
    name="Traffic Control System",
    description="""A smart traffic management system with sensors, traffic light
controllers, and route planners coordinating to optimize traffic flow.""",
    agents=[
        AgentDef(
            id="sensor",
            name="Traffic Sensor",
            description="Reads vehicle count and speed from road sensors and emits data. No internal state or memory.",
            attributes=[
                AgentAttribute(name="internal_state", value="none", description="Stateless emitter"),
                AgentAttribute(name="planning_horizon", value="none"),
                AgentAttribute(name="memory", value="none"),
                AgentAttribute(name="decision_logic", value="if_then"),
                AgentAttribute(name="adaptability", value="none"),
                AgentAttribute(name="sensing", value="direct"),
            ],
        ),
        AgentDef(
            id="controller",
            name="Traffic Light Controller",
            description="Models traffic patterns and adjusts signal timing based on sensor data and historical trends.",
            attributes=[
                AgentAttribute(name="internal_state", value="full", description="Maintains signal phase state and timing tables"),
                AgentAttribute(name="planning_horizon", value="long_term"),
                AgentAttribute(name="memory", value="long_term"),
                AgentAttribute(name="decision_logic", value="utility"),
                AgentAttribute(name="adaptability", value="medium"),
                AgentAttribute(name="sensing", value="indirect"),
            ],
        ),
        AgentDef(
            id="planner",
            name="Route Planner",
            description="Analyzes road network topology and traffic data to recommend optimal routes for emergency vehicles.",
            attributes=[
                AgentAttribute(name="internal_state", value="full", description="Maintains road network graph"),
                AgentAttribute(name="planning_horizon", value="long_term"),
                AgentAttribute(name="memory", value="long_term"),
                AgentAttribute(name="decision_logic", value="utility"),
                AgentAttribute(name="adaptability", value="low"),
                AgentAttribute(name="sensing", value="indirect"),
            ],
        ),
    ],
    interactions=[
        InteractionDef(
            source="sensor",
            target="controller",
            label="sends sensor readings",
            type=InteractionType.data_flow,
        ),
        InteractionDef(
            source="controller",
            target="planner",
            label="transmits traffic data",
            type=InteractionType.data_flow,
        ),
        InteractionDef(
            source="planner",
            target="controller",
            label="provides route recommendations",
            type=InteractionType.feedback_loop,
        ),
    ],
)
