# Feature Specification: Flowise Multi-Agent Course Guide

**Feature Branch**: `005-flowise-guide`

**Created**: 2026-08-06

**Status**: Draft

**Input**: "Trabajemos en las tareas descritas en el documento 'Course-end Project - AI agents - multi-agent design and governance.pdf'. Se necesita crear una guía paso a paso para desarrollar el ejercicio en la plataforma Flowise mediante una instancia local en docker (docker-flowise-1), con fuentes en C:\working\projects\ai-projects\Flowise."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build the Three Specialist Agent Chatflows (Priority: P1)

As a learner enrolled in the course, I want a step-by-step guide that walks me through creating each of the three specialist chatflows inside my local Flowise instance, so that I can build the foundations of the e-commerce support crew.

**Why this priority**: Without the three specialist agents there is nothing for the orchestrator to route to. It is the prerequisite for the entire project and for Deliverable 1 (screenshot of the canvas).

**Independent Test**: Can be fully tested by following the guide from a fresh Flowise instance and verifying that three separately named chatflows ("Product Agent", "Order Agent", "Promotions Agent") exist and each returns a coherent answer to a probe question when invoked in chat.

**Acceptance Scenarios**:

1. **Given** a developer has a running local Flowise instance, **When** they follow the guide's Part 1 steps, **Then** they create a chatflow named "Product Agent" that answers generic product questions using the persona of a product expert
2. **Given** a running local Flowise instance, **When** the learner follows Part 1, **Then** they create a chatflow named "Order Agent" that asks for an order number and replies with a simulated static delivery estimate
3. **Given** a running local Flowise instance, **When** the learner follows Part 1, **Then** they create a chatflow named "Promotions Agent" that acts as a sales assistant and states a fictional current sale
4. **Given** a specialist chatflow is open, **When** the learner sends a matching probe question in its chat canvas, **Then** the agent returns a coherent on-topic answer confirming its persona

---

### User Story 2 - Building the Orchestrator (Priority: P1)

I want the guide to explain how to assemble the central orchestrator chatflow that routes user queries to the correct specialist agent, since this orchestrator is the project's main deliverable and the subject of the grading screenshot.

**Why this priority**: The orchestrator with a routing node and its three connections is the explicit artifact requested in Deliverable 1; without it no submission screenshot can be produced.

**Acceptance Scenarios**:

1. **Given** the three specialist chatflows exist, **When** the learner follows Part 2, **Then** they create a primary orchestrator chatflow as a single point of contact
2. **Given** the orchestrator chatflow is **When** the learner adds a routing node, **Then** it exposes routes named `product_info`, `order_status`, and `promotions` with clear descriptions for the router
3. **Given** routes are defined, **When** the learner wires each route to the correct specialist chatflow, **Then** the orchestrator canvas shows the central routing node connected to at least the three specialist agents
4. **Given** the wired orchestrator, **When** the learner posts queries of three different intents through its chat, **Then** each query is dispatched to the correct corresponding specialist agent

---

### User Story 3 - Draft the Four Written Deliverables (Priority: P3)

I want the guide to give me chapter structures and prompts to author the four written deliverables (architecture, methodology, risk & governance, reflection), so that I can finalize the submission document for AI grading without inventing a report skeleton from scratch.

**Acceptance Scenarios**:

1. **Given** the built orchestrator, **When** the learner follows Part 3, **Then** they can produce the four deliverables: architecture screenshot, design methodology (150-200 words), risk & governance analysis (200-300 words), and a reflection (250 words)
2. **Given** a draft of each deliverable, **When** the learner compiles the report, **Then** it is saved as a single PDF covering all four sections for upload

---

### Edge Cases

- What happens when a probe query is ambiguous and could match two specialist intents? (The guide should explain how the routing node's route descriptions bias the decision.)
- What happens when the learner has no LLM API credential ready before building chatflows? (The guide's setup section must show where to configure the model provider credential in the instance.)What settings such as model name differ between specialist chatflow vs orchestrator? (The guide should list model/prompt settings to check to avoid empty responses.)
- What happens if a learner has no prior Flowise experience and is unfamiliar with the canvas UI? (The guide's setup and navigation section must orient the reader before they build.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guide MUST provide an overview of the assignment scenario, tools, and the four learning objectives and four grading deliverables
- **FR-002**: The guide MUST include a setup section covering the local instance on its origin: verifying and accessing the local Flowise via `http://localhost:3000`
- **FR-003**: The guide MUST show where to configure the model/LLM credential and selected model within the local instance, since no provider is predefined
- **FR-004**: The guide MUST provide a visual architecture sketch of the crew: one orchestrator plus three specialist agents (Product Info, Order Status, Promotions)
- **FR-005**: The guide MUST give step-by-step instructions to create the "Product Agent" chatflow with an LLM Chain that adopts a product-expert persona
- **FR-006**: The guide MUST give step-by-step instructions to create the "Order Agent" chatflow configured to ask for the order number and return a static simulated delivery estimate
- **FR-007**: The guide MUST give step-by-step instructions to create the "Promotions Agent" chatflow configured as a sales assistant returning a fictional promotional offer
- **FR-008**: The guide MUST instruct saving each chatflow under a clean, distinctive name
- **FR-009**: The guide MUST give steps to create the central orchestrator and add a routing node (a multi-prompt router) used as the "brain"
- **FR-010**: The guide MUST define the three route names and route descriptions that the router uses to dispatch intents (product features, order status, promotions)
- **FR-011**: The guide MUST show how to connect each orchestrator route to the corresponding specialist chatflow node so the final canvas links the orchestrator to the specialists
- **FR-012**: The guide MUST include a testing checklist of probes sentences (one per intent) to verify routing correctness through the orchestrator chat
- **FR-013**: The guide MUST provide the structure and drafts for the four written deliverables as target text for Degree1 Method2 etc.
- **FR-014**: The guide MUST list the submission files and formats mandated by the assignment: `PNG/JPG/JPEG` screenshot, and a `PDF/DOCX/TXT` report, and the peer-review sharing steps
- **FR-015**: The guide MUST be written in a single accessible step-by-step document (Markdown) collated within the `Flowise` source or, with the instance's repo as the source of truth.

### Key Entities *(include if feature involves data)*

- **Specialist Agent**: A self-contained Flowise chatflow (Product, Order Status, Promotions) with its own prompt/persona
- **Orchestrator Agent**: the primary chatflow acting as the user's single point of contact, holding the routing node and its connections
- **Router**: the routing node that analyzes user intents and decides which specialist to route a query to based on route names and descriptions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A learner with the local instance can follow the guide and create the three specialist chatflows in under 40 minutes
- **SC-002**: Each of the three specialist chatflows responds coherently to its intended intent and stays on-subject (verified by one probe each)
- **SC-003**: The orchestrator canvas contains one central routing node connected to the three specialist chatflows (Deliverable 1 screenshot requirement)
- **SC-004**: The orchestrator routes each of the three probe intents to the correct specialist 100% of the time in testing
- **SC-005**: The guide provides structure for all four written deliverables; the compiled report is a single PDF covering Deliverables 2-4
- **SC-006**: The guide can be followed end-to-end without consulting any external how-to material beyond the assignment document

## Assumptions

- The local instance is the running Docker container `docker-flowise-1` (image `flowiseai/flowise:3.1.3`), reachable at `http://localhost:3000`
- The learner has already started/verified the container; the guide accounts for accessing it and, if needed, the Docker startup command is captured as reference from the `C:\working\projects\ai-projects\Flowise` repo
- No LLM provider credential is predetermined; the guide avoids hardcoding keys and instructs creating a provider credential within the ChatUse UI (provider-agnostic)
- The guide is written in English to be reusable by the course, or in the same language as the assignment materials (course content is in English)
- All three specialist chatflows use the same underlying LLM provider; differences are in the prompt/personas, not in tooling
- The e-commerce subject is "Future Gadgets Inc." with three support query categories: product information, order status, promotions & deals
- The simulated response for order status and the fictional promotion (e.g., 20% off smartwatches) are invented by the student and only illustrative
- Source of truth for environment placeholders is `C:\working\projects\ai-projects\Flowise` (docker-compose, README, `.env.example`); the guide references these, not sells specific secrets
- Scope boundary: the guide implements ChatFlow/chatflows only; it does not build a production-grade backend, database integration, or web chat widget embedding unless the assignment explicitly demands them
- Dependency: an internet connection and an active LLM API credential are required at run-time to produce model responses for testing the chatflows