# Feature Specification: Agent Ecosystem Mapping

**Feature Branch**: `003-agent-ecosystem-mapping`

**Created**: 2026-07-17

**Status**: Draft

**Input**: "Trabajemos en las tareas descritas en el documento HOL - module 1.pdf"

The work should be implemented at src/multiagent-governance_course/module_1_foundations.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Agents by Type (Priority: P1)

As a learner, I want to classify AI agents into reactive, deliberative, or hybrid categories based on their attributes and behavior, so that I can understand how agent type selection affects system design.

**Why this priority**: Classification is the foundational skill — all subsequent analysis and mapping depends on correctly identifying agent types.

**Independent Test**: Can be fully tested by providing agent descriptions and verifying the classification output matches expected types.

**Acceptance Scenarios**:

1. **Given** a description of a stateless agent (e.g., "reads sensor data and emits it without state"), **When** the system classifies it, **Then** the output is "Reactive" with a justification referencing statelessness
2. **Given** a description of a deliberative agent (e.g., "models the road network and plans optimal routes"), **When** the system classifies it, **Then** the output is "Deliberative" with a justification referencing world modeling
3. **Given** a description with mixed reactive and deliberative traits, **When** the system classifies it, **Then** the output is "Hybrid" with justification referencing both attributes

---

### User Story 2 - Map Agent Interactions in a Scenario (Priority: P1)

As a learner, I want to visualize how multiple agents interact in a shared environment (e.g., a traffic control system), so that I can understand data flow and coordination patterns between different agent types.

**Why this priority**: Interaction mapping builds on classification and is the core deliverable of Activity 1.

**Independent Test**: Can be fully tested by providing agent roles and verifying the generated interaction diagram includes correct labeled nodes, directed arrows, and data flow annotations.

**Acceptance Scenarios**:

1. **Given** a set of agents (Sensor, Traffic Light Controller, Route Planner) with defined roles, **When** the system generates an interaction map, **Then** it shows data flow from Sensor → Traffic Light Controller → Route Planner with labeled arrows
2. **Given** two agents with a bidirectional relationship, **When** the system maps interactions, **Then** it includes feedback loops with appropriate annotations
3. **Given** agents with no direct interaction, **When** the system maps interactions, **Then** it omits connections between them

---

### User Story 3 - Analyze Agent Type Trade-offs (Priority: P2)

As a learner, I want to analyze how reactive versus deliberative agent choices affect system speed, accuracy, and resilience, so that I can make informed architectural decisions.

**Why this priority**: Analysis demonstrates deeper understanding beyond classification and is required for Activity 1 Deliverable 3.

**Independent Test**: Can be tested by providing a system description and verifying the analysis covers speed, scalability, and decision quality trade-offs.

**Acceptance Scenarios**:

1. **Given** a mixed reactive-deliberative system, **When** the learner submits an analysis, **Then** it identifies at least one speed advantage of reactive agents and one accuracy advantage of deliberative agents
2. **Given** a system failure scenario, **When** the learner analyzes resilience, **Then** they identify how reactive agents are more robust and deliberative agents are potential single points of failure

---

### User Story 4 - Model Core Agent Capabilities (Priority: P2)

As a learner, I want to define and diagram the perception-reasoning-action cycle of a single AI agent (e.g., a personal task manager), so that I understand the core capabilities that enable autonomous behavior.

**Why this priority**: This introduces fundamental agent architecture before multi-agent coordination, as described in Activity 2.

**Independent Test**: Can be tested by providing a scenario (e.g., weather-caused meeting reschedule) and verifying the diagram shows a complete perception → reasoning → action cycle with annotations.

**Acceptance Scenarios**:

1. **Given** a personal assistant scenario with a weather conflict, **When** the system models perception, **Then** it identifies calendar and weather API data as inputs
2. **Given** perceived environmental changes, **When** the system models reasoning, **Then** it evaluates multiple alternatives and selects the best action
3. **Given** a reasoned decision, **When** the system models action, **Then** it executes changes via appropriate tools

---

### Edge Cases

- What happens when an agent exhibits traits of multiple types with equal weight?
- How does the system handle scenarios where agents have overlapping or conflicting responsibilities?
- What happens when sensor data is incomplete or unreliable?
- How does a deliberative agent handle situations where its world model is outdated?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST classify agents as Reactive, Deliberative, or Hybrid using a hybrid approach — rule-based decision tree for unambiguous cases, LLM fallback for ambiguous cases — with a supporting justification
- **FR-002**: System MUST generate interaction maps in Mermaid format showing directed data flow between agents with labeled edges
- **FR-003**: System MUST support bidirectional relationships and feedback loops in interaction maps
- **FR-004**: System MUST produce trade-off analysis covering speed, accuracy, scalability, resilience, and adaptability for each agent type
- **FR-005**: System MUST model the perception-reasoning-action cycle for a single agent scenario (Activity 2)
- **FR-006**: System MUST allow learners to define custom agent attributes for classification
- **FR-007**: System MUST generate side-by-side comparisons of purely reactive, purely deliberative, and hybrid system designs
- **FR-008**: System MUST support scenario-based learning with predefined scenarios (traffic control for Activity 1, personal task management for Activity 2)
- **FR-009**: System MUST compile all 4 deliverables (classification table, interaction diagram, trade-off analysis, reflection) into a single file formatted for Coursera upload and AI grading
- **FR-010**: System MUST present an interactive web interface where learners input agent descriptions and receive classification, interaction maps, and analysis in real time
- **FR-011**: System MUST include a "Generate Submission" feature that compiles the current session's deliverables into a single file with all sections required by Coursera grading criteria
- **FR-012**: System MUST offer both .md and .pdf download formats for the compiled submission
- **FR-013**: System MUST render interaction diagrams and capability cycle diagrams as visual graphics in the PDF (not as raw Mermaid code blocks), using graph layout positioning and vector drawing primitives

### Key Entities *(include if feature involves data)*

- **Agent**: An AI entity with a type (Reactive, Deliberative, Hybrid), attributes (state, planning horizon, memory, decision logic), and a description of its role
- **Interaction**: A directed relationship between two agents with a label describing the data or control flow
- **Scenario**: A real-world context (traffic control, personal scheduling) that defines the environment where agents operate
- **AgentAttribute**: A measurable characteristic used for classification (internal state, planning horizon, decision logic, memory, adaptability)
- **Capability**: A core function of a single agent (perception, reasoning, action) that forms the perception-reasoning-action cycle

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Learners can classify an agent in under 30 seconds given a structured description of its attributes
- **SC-002**: Generated interaction maps correctly represent all agent relationships for a given scenario with 100% accuracy
- **SC-003**: Trade-off analyses cover at least 4 out of 5 dimensions (speed, accuracy, scalability, resilience, adaptability)
- **SC-004**: Perception-reasoning-action diagrams include all three capabilities with labeled transitions
- **SC-005**: Learners can complete all 4 deliverables in under 45 minutes
- **SC-006**: Classification accuracy matches expert-provided ground truth for at least 90% of test cases
- **SC-007**: Generated submission file includes all 4 deliverables (classification table, interaction diagram, trade-off analysis, reflection) in a single document
- **SC-008**: Classification justifications in the submission explicitly reference reactive, deliberative, or hybrid type names
- **SC-009**: Interaction diagram in the submission has labeled nodes and directed arrows with data flow annotations
- **SC-010**: Submission can be downloaded as both .md and .pdf formats

## Assumptions

- Learners have basic understanding of AI concepts (no need to explain what an agent is)
- The traffic control scenario (Sensor Agent, Traffic Light Controller, Route Planner) is the primary use case for Activity 1
- The personal task manager (weather-based rescheduling) is the primary use case for Activity 2
- Output formats target AI grading systems that expect structured data (tables, diagrams with labels)
- The system will be used in a Coursera course context with peer review capabilities
- Classification uses a hybrid engine: rule-based decision tree for clear-cut cases, LLM (via LangGraph) for ambiguous cases
- All interface text and generated content is in English
- Diagrams are represented as Mermaid code blocks in the .md file
- The .md and .pdf files must be self-contained — all deliverables, justifications, and diagrams in one document
- PDF diagrams use `grandalf` for graph node positioning and `pymupdf` for drawing shapes, text, and arrows — no new external dependencies

## Clarifications

### Session 2026-07-17

- Q: How should Mermaid diagrams be rendered in the generated PDF? → A: Use `grandalf` for graph layout (node positioning) + `pymupdf` primitives (shapes, text, arrows) for drawing. This avoids new external dependencies per Constitution VI and gives full control over visual output.
