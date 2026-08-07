# LangGraph Framework — Coursera Course

Workbook for the [LangGraph Framework](https://www.coursera.org/learn/langgraph-framework) course on Coursera.

## LinkedIn Summary

**LangGraph Framework — Multi-Agent Systems & Stateful LLM Workflows**

Built production-grade multi-agent AI systems using LangGraph, LangChain, and LangSmith. Implemented 9 multi-agent coordination patterns (coordinator, specialist, event-driven, ReAct, reflection, planning, tool, sequential, human-in-the-loop) across 11 standalone graph implementations with unified support-ticket domain, `@timed_node` observability, and `interrupt()`/`MemorySaver` checkpointing.

**Key skills demonstrated**:

- **Agentic AI Architecture** — Designed typed state schemas, conditional routing, and cyclic graphs for dynamic multi-agent orchestration
- **State Management** — Implemented persistent shared state across 5-agent workflows with provenance chaining, conflict detection, circuit breakers, and graceful degradation
- **Observability** — Wired `@timed_node` telemetry, structured loguru logging, and `TelemetryEvent` records into every node; built real-time Streamlit streaming UI
- **Resilience Patterns** — Exponential backoff retry, input refinement gates, execution budget enforcement, and 3-strike circuit breakers routed via LangGraph conditional edges
- **Enterprise Patterns** — Checkpointing, interrupt/resume approval gates, per-thread workflow isolation, and modular pluggable agent nodes
- **Testing & Quality** — 35+ unittest test cases across state validation, node isolation, conflict resolution, routing logic, and end-to-end integration (3+ workflow paths)
- **Production Readiness** — `ruff` linting, Black formatting, pydantic-settings config, and `LLMFactory` provider abstraction (OpenRouter, OpenAI, Anthropic)

**Stack**: Python 3.10+ · LangGraph · LangChain · LangSmith · pydantic · loguru · Streamlit · Poetry

## What You Learn By Module

### Module 1 — LangGraph Architecture & Core Concepts
- **StateGraph fundamentals** — typed state schemas, nodes, edges, conditional edges
- **Workflow composition** — entry/finish points, linear vs branching topologies
- **Conditional routing** — keyword-based classification, dynamic edge targets
- **Testing discipline** — writing `unittest` tests before implementation, test-driven graph development
- **Builds**: chatbot, intent classifier, support-ticket triage agent

### Module 2 — State Management & Resilience
- **State design** — modeling complex state with `pydantic.BaseModel`, state transitions, lifecycle enums
- **Error handling** — structured `ErrorRecord` logging, gracefully degraded states (`processing_outcome="partial"`)
- **Retry patterns** — exponential backoff for transient API failures, configurable retry budgets
- **Observability** — per-node latency tracking with `@timed_node`, audit-trail accumulation in state
- **Builds**: resilient legal document processor with compliance tracking

### Module 3 — Multi-Agent Systems
- **9 coordination patterns** — when to use coordinator vs specialist vs event-driven vs ReAct vs reflection vs planning vs tool vs sequential vs human-in-the-loop
- **Shared state** — cross-agent awareness via a single `BaseModel` state schema, provenance chains, finding attribution
- **Resilience at scale** — circuit breaker (3-strike bypass), conflict detection/resolution, execution budget enforcement, graceful degradation
- **Production patterns** — `interrupt()`/`Command()` for human-in-the-loop, `MemorySaver` checkpointing, thread isolation
- **Streaming UIs** — real-time agent card updates via `StateGraph.stream()` with Streamlit
- **Builds**: 11 standalone pattern implementations + 5-agent research system (Research, Financial, Market, Risk, Synthesis)

### Module 4 (Capstone) — Production-Ready Multi-Agent System
- **Emergent intelligence** — agent collaboration producing insights no single agent can generate
- **Full observability** — `@timed_node` + loguru + `TelemetryEvent` records in shared state
- **Advanced resilience** — circuit breaker, input refinement, LLM-based conflict resolution, retry with backoff
- **Documentation** — architecture docs, reflection report, 3+ workflow path integration tests

## Overview

LangGraph is a framework for building stateful, multi-actor applications with Large Language Models (LLMs). It extends
LangChain by adding the ability to define cyclic graphs, enabling agent loops, tool-calling, and complex multi-step
reasoning workflows.

> AI coding assistants working on this repo should read [`AGENTS.md`](AGENTS.md) for conventions, testing setup, and
> agent behavior guidelines.

## Project Structure

```
src/langgraph_course/
├── config.py                # Shared configuration (API keys, model settings)
├── models.py                # Shared TypedDicts / Pydantic models
├── log.py                   # Loguru configuration
├── utils/
│   ├── llm.py               # LLMFactory — sync (LangChain) and async (direct SDK)
│   ├── graph.py             # Graph visualization helpers
│   ├── decorators.py        # Shared timed_node decorator for per-node telemetry
│   └── providers/           # Provider registry for LLM backends
│       ├── base.py          #   BaseProvider ABC + register_provider
│       ├── openrouter.py    #   OpenRouter (AsyncOpenAI)
│       ├── openai_provider.py   #   OpenAI (AsyncOpenAI)
│       └── anthropic_provider.py # Anthropic (AsyncAnthropic)
├── module_1/                # Understanding LangGraph Architecture
│   └── labs/
│       ├── __init__.py
│       ├── chatbot.py       # Simple chatbot graph
│       ├── customer_inquiry.py  # Intent-classification agent
│       ├── tickets.py       # Support-ticket routing with retry logic
│       ├── ticket_submission.txt  # Coursera reflection submission
│       └── data.py          # Shared test data
├── multiagent-governance_course/  # Agent Ecosystem Mapping + Sequential Agent Workflows
│   ├── module_1_foundations/      # Module 1: agent classification, interaction maps, trade-off analysis
│   └── module_2_multiagents/      # Module 2: sequential Researcher -> Writer -> SEO blog pipeline
│       ├── agents/
│       │   ├── prompts.py         # Researcher/Writer/SEO prompt templates + LLM invocation
│       │   ├── researcher.py      # Node: topic -> bulleted outline
│       │   ├── writer.py          # Node: outline -> article draft
│       │   └── seo.py             # Node: draft -> SEO feedback
│       ├── state.py               # BlogState pydantic model
│       ├── workflow.py            # Linear LangGraph StateGraph chain
│       ├── runtime.py             # run_pipeline() façade
│       ├── export.py              # Prompt-engineering doc + communication-protocol analysis
│       └── __main__.py            # CLI entry point
├── module_2/                # Implementing State Management
│   └── labs/
│       ├── __init__.py
│       ├── legal_documents.py  # Resilient doc processing with error handling
│       ├── legal_submission.txt  # Coursera reflection submission
│       ├── resilient-state-design.md  # Design document
│       └── C63_*.pdf        # Lab exercise guide
├── module_3/                # Building Multi-Agent Systems
│   └── labs/
│       └── patterns/
│           ├── coordinator.py                 # Coordinator: hub-and-spoke with human review
│           ├── coordinator_cafe.py            # Cafe-domain variant of the coordinator pattern
│           ├── specialist.py                  # Specialist: fully-connected mesh
│           ├── event_driven_collaboration.py  # Event-driven: pub-sub event bus
│           ├── react.py                      # ReAct: single-agent reasoning + tool calling
│           ├── reflection.py                 # Reflection: generate → critique → refine loop
│           ├── reflection_cafe.py            # Cafe-domain variant of the reflection pattern
│           ├── planning.py                   # Planning: plan → execute → review → repeat
│           ├── tool.py                       # Tool: classify → run tool → format response
│           ├── sequential.py                 # Sequential: fixed-order linear pipeline
│           └── human_in_the_loop.py          # Human-in-the-Loop: human collaborates at key points
├── agents/                  # Tool-calling agents
│   ├── cafe_agent.py        # 2-node LangGraph tool-calling graph
│   ├── cafe/
│   │   ├── models.py        # Pydantic models (Customer, Order, MenuOptions, etc.)
│   │   ├── tools.py         # Tool functions (get_daily_menu, create_order, etc.)
│   │   └── prompts.py       # System prompts for agent behavior
│   └── weather_agent.py     # Weather agent with HTTP tool support
tests/
├── base.py                  # Shared TestCase with setUp/tearDown helpers
├── multiagent-governance_course/
│   ├── test_module_1_foundations/
│   │   ├── test_analysis.py
│   │   ├── test_classification.py
│   │   ├── test_export.py
│   │   ├── test_interaction_map.py
│   │   └── test_scenarios.py
│   └── test_module_2_multiagents/
│       ├── test_agents.py
│       ├── test_export.py
│       ├── test_prompts.py
│       ├── test_state.py
│       └── test_workflow.py
├── test_module_1/
│   ├── test_chatbot.py
│   ├── test_customer_inquiry.py
│   └── test_tickets.py
├── test_module_2/
│   └── test_legal_documents.py  # 71 tests covering nodes, routing, error handling
├── test_module_3/
│   ├── test_coordinator.py       # 38 tests for coordinator pattern
│   └── test_coordinator_cafe.py  # 32 tests for cafe coordinator variant
├── test_agents/
│   └── test_cafe_agent.py
└── test_utils/
    └── test_llm.py
```

## How to Work on an Exercise

Each module has a `labs/` directory with exercise files. Each exercise follows this pattern:

1. **Scaffold** — the exercise file (`module_X/labs/exercise_name.py`) provides stub functions with type signatures and
   docstrings.
2. **Tests** — the matching test file (`tests/test_module_X/test_exercise_name.py`) defines what each function should
   do.
3. **Implement** — fill in the function bodies in the exercise file.
4. **Verify** — run the tests to check your implementation.

```bash
# Run tests for a specific exercise
poetry run python -m unittest tests.test_module_1.test_customer_inquiry -v

# Run all tests
poetry run python -m unittest discover -v
```

## Flowise Course-end Project Guide

The course-end project ("Designing an Autonomous E-commerce Support Crew") is implemented as a **step-by-step guide** for building the multi-agent system on a local Flowise instance (Docker container `docker-flowise-1`, UI at `http://localhost:3000`). See:

- **[Guide](docs/flowise-course-end-project/README.md)** — build the three specialist agents, the orchestrator with a routing node, and author the four grading deliverables
- **[Feature spec](specs/005-flowise-guide/spec.md)** — requirements, user stories, and success criteria
- **[Design docs](specs/005-flowise-guide/)** — `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

> The guide references the Flowise source checkout at `C:\working\projects\ai-projects\Flowise` as the source of truth for node names and configuration.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
poetry install
```

### API Keys

Copy the environment template and fill in your LLM provider key:

```bash
cp .env.example .env
```

Then edit `.env` with your API key(s). Available providers and their required fields:

| Provider   | `llm_provider` | Required env vars                           |
|------------|----------------|---------------------------------------------|
| OpenRouter | `"openrouter"` | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` |
| OpenAI     | `"openai"`     | `LLM_API_KEY`                               |
| Anthropic  | `"anthropic"`  | `LLM_API_KEY`                               |

The `config.py` loader reads these automatically at import time.

## Calling a Provider

Use `LLMFactory.call()` to make an async LLM call — it dispatches to the correct provider based on
`settings.llm_provider`:

```python
import asyncio
from utils import LLMFactory

response = asyncio.run(LLMFactory.call("What is LangGraph?"))
print(response)
```

Or switch providers at the call site:

```python
response = asyncio.run(LLMFactory.call("Hello", provider="openrouter"))
```

For synchronous LangChain-based usage, use `LLMFactory.create()`:

```python
llm = LLMFactory.create(provider="openrouter")
result = llm.invoke("Hello")
```

Each provider can also be used independently:

```python
from utils.providers.openrouter import OpenRouterProvider

provider = OpenRouterProvider()
response = asyncio.run(provider.call("Hello"))
```

## Running Tests

```bash
# Run all tests
poetry run python -m unittest discover -v

# Run tests for a specific module
poetry run python -m unittest tests.test_module_1 -v
poetry run python -m unittest tests.test_module_2 -v

# Run tests for Module 1 Foundations (hyphenated path — use -t .)
python -m unittest discover -s tests/multiagent-governance_course/test_module_1_foundations -t . -v

# Run tests for a specific exercise
poetry run python -m unittest tests.test_module_1.test_customer_inquiry -v
poetry run python -m unittest tests.test_module_2.test_legal_documents -v
```

## Streamlit UI

A multi-agent Streamlit app lets you interact with the agents through a chat interface:

```bash
poetry run streamlit run streamlit_app.py
```

Available agents:

- **☕ Cafe** — Tool-calling menu ordering assistant
- **🌤 Weather** — Live weather forecast agent
- **📄 Legal Docs** — Resilient document processing with error handling, compliance tracking, and audit trail
  visualization

# Multi-Agent System Patterns

Module 3 explores nine multi-agent coordination strategies, each implemented as a standalone LangGraph graph with the
same support-ticket domain (billing, technical, general) and consistent infrastructure (`timed_node`, `interrupt()`/
`Command()`, `MemorySaver`).

> Based on the framework from [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/).
> See also the enterprise architecture white paper: [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/)

| Pattern | Communication | Routing Authority | Cross-Agent Flow |
|---|---|---|---|---|
| **Coordinator** | Hub-and-spoke | Central `coordinator` re-classifies every round | Coordinator reads agent response
keywords |
| **Specialist** | Fully-connected mesh | Each specialist decides `route_to` | Specialist reads original `query` |
| **Event-Driven** | Pub-sub event queue | Event bus dispatches by event type subscription | Agent publishes events of
different types |
| **ReAct** | Single-agent loop | Agent decides tool-to-call or respond | Agent calls tools → reads result → responds |
| **Reflection** | Generate → critique → refine | Critic evaluates and approves/revises | Generator produces draft,
critic provides feedback |
| **Planning** | Plan → execute → review → repeat | Planner creates and tracks progress on ordered steps | Planner
decomposes query, executor runs each step |
| **Tool** | Classify → run tool → format | Orchestrator selects single tool, formatter responds | Linear pipeline — one
tool call, no loop |
| **Sequential** | Fixed-order linear pipeline | Each agent passes output to next in fixed sequence | Strict ordering —
no
routing, no loops |
| **Human-in-the-Loop** | Human-classify → agent → human-approve | Human decides topic and approves/rejects output |
Human classifies,
reviews, and provides revision feedback |

## Files

| File | Pattern | Domain | Agents / Tools |
|---|---|---|---|---|
| [`coordinator.py`](src/langgraph_course/module_3/labs/patterns/coordinator.py) | Coordinator | Support tickets |
agent\_a (billing), agent\_b (technical), agent\_c (general) |
| [`coordinator_cafe.py`](src/langgraph_course/module_3/labs/patterns/coordinator_cafe.py) | Coordinator | Cafe |
menu\_agent, order\_agent, customer\_agent |
| [`specialist.py`](src/langgraph_course/module_3/labs/patterns/specialist.py) | Specialist | Support tickets |
agent\_a, agent\_b, agent\_c |
| [`event_driven_collaboration.py`](src/langgraph_course/module_3/labs/patterns/event_driven_collaboration.py) |
Event-Driven | Support tickets | agent\_a, agent\_b, agent\_c |
| [`react.py`](src/langgraph_course/module_3/labs/patterns/react.py) | ReAct | Support tickets | lookup\_invoice,
check\_system\_status, escalate\_to\_human (tools) |
| [`reflection.py`](src/langgraph_course/module_3/labs/patterns/reflection.py) | Reflection | Support tickets |
generator, critic |
| [`reflection_cafe.py`](src/langgraph_course/module_3/labs/patterns/reflection_cafe.py) | Reflection | Cafe |
generator, critic |
| [`planning.py`](src/langgraph_course/module_3/labs/patterns/planning.py) | Planning | Support tickets | planner,
executor |
| [`tool.py`](src/langgraph_course/module_3/labs/patterns/tool.py) | Tool | Support tickets | tool\_orchestrator,
tool\_invoice, tool\_status, tool\_escalate, output\_formatter |
| [`sequential.py`](src/langgraph_course/module_3/labs/patterns/sequential.py) | Sequential | Support tickets |
analyzer, specialist, formatter |
| [`human_in_the_loop.py`](src/langgraph_course/module_3/labs/patterns/human_in_the_loop.py) | Human-in-the-Loop |
Support tickets |
human\_classify, agent, human\_approve |

## Running

```bash
# Run samples
poetry run python -m src.langgraph_course.module_3.labs.patterns.coordinator
poetry run python -m src.langgraph_course.module_3.labs.patterns.coordinator_cafe
poetry run python -m src.langgraph_course.module_3.labs.patterns.specialist
poetry run python -m src.langgraph_course.module_3.labs.patterns.event_driven_collaboration
poetry run python -m src.langgraph_course.module_3.labs.patterns.react
poetry run python -m src.langgraph_course.module_3.labs.patterns.reflection
poetry run python -m src.langgraph_course.module_3.labs.patterns.reflection_cafe
poetry run python -m src.langgraph_course.module_3.labs.patterns.planning
poetry run python -m src.langgraph_course.module_3.labs.patterns.tool
poetry run python -m src.langgraph_course.module_3.labs.patterns.sequential
poetry run python -m src.langgraph_course.module_3.labs.patterns.human_in_the_loop

# Run tests (coordinator + cafe have tests; specialist, event-driven, react, reflection, reflection_cafe, planning, tool, sequential, and human_in_the_loop are untested)
poetry run python -m unittest tests.test_module_3.test_coordinator -v
poetry run python -m unittest tests.test_module_3.test_coordinator_cafe -v
```

## Coordinator Pattern

A central coordinator classifies messages and routes them to specialist agents.

### Architecture

```
coordinator → human_review → agent_* → coordinator (or END)
```

- **coordinator**: Classifies the last message via keyword matching and sets `next_agent`.
- **human_review**: Pauses via `interrupt()` — human can `approve` (route to agent), `redirect` (back to coordinator for
  re-classification), or `end` (terminate workflow).
- **agents**: Each specialist processes the request, then routes back to coordinator for re-classification (if
  incomplete) or to `END` (if done).

### Key Design Decisions

- **Agents decide when to end**, not the coordinator — each agent has a conditional edge to either `coordinator` or
  `END`.
- **Coordinator never routes directly to `END`** — only agents can terminate the workflow.
- **`MAX_ROUNDS` safety valve** forces `task_complete=True` on any agent after 4 rounds, preventing infinite loops.
- **Cross-agent routing** works via agent response messages containing keywords that trigger re-classification by the
  coordinator on the next round.
- **Human-in-the-loop** uses LangGraph's `interrupt()`/`Command()` with a `MemorySaver` checkpointer, enabling approval,
  redirect, or termination at each routing decision.

## Specialist Pattern

The inverse of the coordinator pattern — specialists route directly to each other in a fully-connected mesh.

### Architecture

```
entry -> human_review -> agent_a <-> agent_b <-> agent_c -> END
```

- **entry**: Classifies the user's query and sets the initial `next_agent`.
- **human_review**: Same `interrupt()` pattern for approve/redirect/end.
- **Each specialist** reads the original query and decides whether to handle it (`task_complete=True` → `END`) or
  delegate (`route_to='agent_X'`).
- **Mesh edges**: Every specialist's conditional edge maps to every agent and `END`, so any specialist can route to any
  other.

### Ambiguous Queries

When a query contains keywords matching multiple specialists (e.g., "technical bug with payment"), the mesh can
ping-pong between agents. `MAX_ROUNDS` prevents infinite loops.

## Event-Driven Collaboration Pattern

Agents communicate through a shared event queue (pub-sub bus). No agent routes to another directly — instead, each
processes events and publishes new events to the bus.

### Architecture

```
entry -> human_review -> event_bus -> subscriber -> event_bus (or END)
                                         ^              |
                                         +----always----+
```

- **entry**: Classifies the query and publishes a domain event (`billing_request`, `technical_request`, or
  `general_request`) to the event queue.
- **human_review**: Approve (proceed to event bus), redirect (back to entry), or end.
- **event_bus**: Reads the next unprocessed event, looks up the subscriber by event type in `SUBSCRIPTIONS`, sets
  `active_subscriber`.
- **agents**: Process the event, advance `event_index` (consume the event), and publish new events to the queue.
- **agent_router**: Always routes back to `event_bus`.
- **event_bus_router**: If unprocessed events remain, routes to the subscriber; otherwise END.

### Event System

```python
SUBSCRIPTIONS = {
    "billing_request": "agent_a",
    "technical_request": "agent_b",
    "general_request": "agent_c",
    "resolution": None,  # No subscriber — terminates
}
```

### Sample Flow

```
User: "I have a billing question about my invoice"
→ entry publishes billing_request
→ human_review approves → event_bus
→ event_bus dispatches billing_request → agent_a
→ agent_a publishes resolution
→ event_bus dispatches resolution → no subscriber → END
```

Cross-agent flow:

```
User: "technical bug with payment"
→ entry publishes billing_request (keyword "payment" matches billing first)
→ agent_a sees "technical bug" in query, publishes technical_request + resolution
→ event_bus dispatches technical_request → agent_b
→ agent_b processes, publishes resolution
→ event_bus dispatches resolution → no subscriber → END
```

## ReAct Pattern

A single agent iteratively reasons about the user's request and calls tools to gather information before responding.
This is the classic LLM agent loop (ChatGPT with plugins, Anthropic tool use).

### Architecture

```
entry -> human_review -> agent <-> tools -> END
                            ↑         |
                            +---loop--+
```

- **entry**: Captures the user query into state.
- **human_review**: Same `interrupt()` gate for approve/redirect/end.
- **agent**: On the first call, classifies the query and decides whether a tool is needed. If yes, sets `tool_to_call`
  and routes to `tools`. On the second call (after `tool_result` is populated), incorporates the tool output into a
  final natural-language response.
- **tools**: Executes the selected tool (`lookup_invoice`, `check_system_status`, `escalate_to_human`) and returns
  structured result data. In production these would call real APIs or databases.
- **agent_router**: `task_complete=True` → END, otherwise → `tools`.
- **tool_router**: Always back to `agent` (unless `MAX_ROUNDS` exceeded).

### Key Design Decisions

- **Single agent, multiple tools** — the pattern demonstrates reasoning through tool use, not multi-agent routing.
- **Agent decides when to stop** — sets `task_complete=True` after either a direct answer or after processing a tool
  result.
- **`MAX_ROUNDS` safety valve** prevents infinite agent↔tools loops.
- **Keyword-based classifier** simulates LLM reasoning so the pattern works without an API key. Swap `_classify_query`
  for a real LLM call to get production-grade tool selection.
- **Human-in-the-loop** uses `interrupt()`/`Command()` with `MemorySaver` checkpointer, same as the other patterns.

## Reflection Pattern

Two roles — a generator and a critic — alternate to iteratively improve a response. The generator produces a draft, the
critic evaluates it and provides feedback, and the generator revises. No external tools or multi-agent routing —
refinement is purely internal.

### Architecture

```
entry -> human_review -> generator -> critic -> generator (or END)
                                ↑         |
                                +---loop--+
```

- **entry**: Captures the user query into state.
- **human_review**: Same `interrupt()` gate for approve/redirect/end.
- **generator**: On the first call, produces an initial draft based on query topic keywords. On subsequent calls,
  revises the draft using the critic's feedback.
- **critic**: Evaluates the current draft. Round 1 drafts are intentionally brief — the critic returns specific
  improvement feedback (issue description, resolution steps, timeline, user action). Round 2+ drafts have been expanded
  and are approved.
- **generator_router**: Always routes to `critic`.
- **critic_router**: Approved → END, otherwise → `generator` (unless `MAX_ROUNDS` exceeded).

### Key Design Decisions

- **Two-role architecture** — separates the creative (generator) and evaluative (critic) functions into distinct nodes,
  reflecting the benefit of distinct system prompts in production systems.
- **Critic sets approval criteria** — only the critic can mark a draft as `approved`. The generator never short-circuits
  the review.
- **`MAX_ROUNDS` safety valve** prevents infinite generate→critique loops.
- **Quality progression** — round 1 drafts are always rejected with structured feedback, demonstrating a concrete
  refinement cycle. Round 2 drafts pass because the simulated revision incorporates the feedback.
- **Human-in-the-loop** uses `interrupt()`/`Command()` with `MemorySaver` checkpointer, same as other patterns.

## Reflection Cafe Pattern

Cafe-domain variant of the reflection pattern. Instead of support-ticket responses, the generator creates menu
recommendations, order confirmations, and customer-service replies while the critic evaluates them for completeness and
specificity.

### Architecture

```
entry -> human_review -> generator -> critic -> generator (or END)
                                ↑         |
                                +---loop--+
```

Same graph topology as the base reflection pattern. Domain-specific differences:

- **generator**: First call produces a brief cafe-themed draft ("We have a great selection today!" / "We received your
  order request."). Subsequent calls expand with specific menu items and prices (Espresso $3.50, Latte $4.50), detailed
  order summaries with pickup times, or a warm welcome message with the full cafe description.
- **critic**: Rejects round 1 drafts shorter than 120 characters with feedback asking for specific items, prices,
  recommendations, and a warm tone. Round 2+ drafts are approved.
- **Topics**: menu, order, customer (delivery/account), and general.

### Key Design Decisions

- **Cafe-specific quality bar** — the critic's threshold (120 chars) is higher than the support-ticket variant (100
  chars) because cafe responses should be more descriptive and inviting.
- **Domain-tailored feedback** — the critic asks for prices, menu items, and a warm tone rather than technical
  resolution steps.
- **Same `MAX_ROUNDS` safety valve** prevents infinite loops regardless of domain.

## Planning Pattern

A planner creates an ordered step-by-step plan to resolve the user's request, an executor runs each step, and the
planner reviews progress after every step. The plan is pre-defined before any execution begins.

### Architecture

```
entry -> human_review -> planner -> executor -> planner (or END)
                                    ↑         |
                                    +---loop--+
```

- **entry**: Captures the user query into state.
- **human_review**: Same `interrupt()` gate for approve/redirect/end.
- **planner**: On the first call, classifies the query and generates a multi-step plan (4 steps for billing/technical, 3
  for general). On subsequent calls, reviews the executor's result, marks the step complete, and advances to the next
  step — or composes a final response when all steps are done.
- **executor**: Runs the current step by looking up a pre-defined result for that step name and topic. In production
  this would call APIs or query a knowledge base.
- **planner_router**: `task_complete=True` → END, otherwise → `executor`.
- **executor_router**: Always routes back to `planner`.

### Sample Flow (Billing)

```
Round 1: planner → Creates 4-step plan: [Verify, Retrieve, Reconcile, Communicate]
Round 2: executor → Runs "Verify customer identity" → result stored
Round 3: planner → Reviews result, advances to "Retrieve invoice"
Round 4: executor → Runs "Retrieve invoice and payment history"
Round 5: planner → Reviews, advances to "Reconcile"
Round 6: executor → Runs "Reconcile billing discrepancy"
Round 7: planner → Reviews, advances to "Communicate"
Round 8: executor → Runs "Communicate resolution"
Round 9: planner → All steps done → composes final response → END
```

### Key Design Decisions

- **Plan-then-execute** — the full plan is created upfront, unlike ReAct (interleaved reasoning and acting).
- **Explicit progress tracking** — `completed_steps` and `step_results` accumulate in state, providing a complete audit
  trail.
- **`MAX_ROUNDS = 6`** — set higher than the default 4 to accommodate multi-step plans.
- **Topic-based step templates** — each topic (billing, technical, general) has a pre-defined plan and step results.
  Swap for LLM-generated plans in production.
- **Human-in-the-loop** uses `interrupt()`/`Command()` with `MemorySaver`.

## Tool Pattern

A linear pipeline that classifies the query, selects a single tool, executes it, and formats the result into a response.
Unlike ReAct (which loops between reasoning and tool use), the Tool pattern is one-shot — no iteration.

Tool use enables agents to perform actions beyond their training data by integrating external capabilities. Agents with
access to tools can call APIs, query databases, execute code, scrape websites, and interact with software systems. The
model orchestrates these capabilities, deciding which tools to invoke based on task requirements, interpreting their
outputs, and chaining tool calls to achieve objectives impossible with static knowledge alone.

### Architecture

```
entry -> human_review -> tool_orchestrator -> [tool_*] -> output_formatter -> END
```

- **entry**: Captures the user query into state.
- **human_review**: Same `interrupt()` gate for approve/redirect/end.
- **tool_orchestrator**: Classifies the query and selects the appropriate tool (`tool_invoice`, `tool_status`, or
  `tool_escalate`). If no tool matches, responds directly.
- **tool_invoice / tool_status / tool_escalate**: Each is a dedicated node that performs one specific operation and
  returns structured data. Tools are one-shot — they run once then route to the formatter.
- **output_formatter**: Reads `tool_result` from state, wraps it in a natural-language response, and sets
  `task_complete=True` → END.
- **orchestrator_router**: If `task_complete` (direct response) → END, otherwise → the selected tool node.
- **tool_router**: Always → `output_formatter`.

### Key Design Decisions

- **Linear pipeline** — no loop or iteration. The query flows through exactly once: classify → tool → format → END.
- **Dedicated tool nodes** — each tool is a separate LangGraph node with a single responsibility, making the graph easy
  to extend (add a new tool = add a node + one conditional edge).
- **Output formatter** separates the raw tool result from the presentation layer. Tools return structured data;
  formatting logic lives in one place.
- **Direct response fallback** — when no tool matches, the orchestrator responds immediately without routing to a tool
  node.
- **Human-in-the-loop** uses `interrupt()`/`Command()` with `MemorySaver`.

## Sequential Pattern

A fixed-order linear pipeline where agents execute one after another in a predetermined sequence. Each agent passes its
output to the next, and the last agent produces the final response. No routing decisions, no loops — the simplest
multi-agent topology.

### Architecture

```
entry -> human_review -> analyzer -> specialist -> formatter -> END
```

- **entry**: Captures the user query into state.
- **human_review**: Same `interrupt()` gate for approve/redirect/end.
- **analyzer**: Classifies the query into billing, technical, or general, extracts key information, and stores the
  analysis in `query_analysis`.
- **specialist**: Reads the analysis and produces a domain-specific response (invoice details, incident report, or
  general acknowledgment).
- **formatter**: Wraps the specialist's output in a polished final message and sets `task_complete=True` → END.
- **human_router**: Approve → `analyzer`, redirect → `entry`, end → END.
- **analyzer_router**: Always → `specialist`.
- **specialist_router**: Always → `formatter`.
- **formatter_router**: Always → END.

### Key Design Decisions

- **No loops** — the flow goes through exactly once, then terminates. Unlike Coordinator (hub re-classifies every round)
  or ReAct (agent↔tools cycles), Sequential is a strict one-pass pipeline.
- **No routing decisions** — each node has exactly one outgoing edge. The topology is hard-coded as part of the pattern.
- **Strict ordering** — agents execute in a fixed, predetermined sequence. You cannot skip or reorder stages at runtime.
- **Each agent has a single responsibility** — the analyzer classifies, the specialist handles, the formatter polishes.
  This makes each node testable in isolation.
- **State carries intermediate outputs** — `query_analysis` and `specialist_response` let downstream agents build on
  upstream work without re-reading raw messages.
- **Human-in-the-loop** uses `interrupt()`/`Command()` with `MemorySaver`, same as other patterns.

## Human-in-the-Loop Pattern

A workflow where humans are active collaborators at key decision points, not just approval gates. The pattern
demonstrates multiple human touchpoints: topic classification, quality review, and revision guidance.

**Use it when**: Decisions involve significant consequences, safety concerns, or subjective judgment that requires human
accountability. Examples:

- Financial transactions exceeding authorization thresholds
- Content moderation for edge cases requiring nuanced judgment
- Legal document approval before filing or signing
- Hiring decisions where AI screens but humans decide

### Architecture

```
entry -> human_classify -> agent -> human_approve -> END
                                   ^              |
                                   +--- loop -----+
```

- **entry**: Captures the user query into state.
- **human_classify** (interrupt #1): The human classifies the query into billing, technical, or general, and can
  optionally provide instructions for the agent.
- **agent**: Generates a domain-specific response based on the human's classification and instructions. If revision
  feedback is present in state, the agent incorporates it.
- **human_approve** (interrupt #2): The human reviews the agent's response. Approve → END, provide feedback → agent
  revises, end → END.
- **human_approve_router**: `approve` or `end` → END, `revise` → agent (with feedback stored in `human_feedback`).

### Key Design Decisions

- **Human is the primary decision-maker** — the human classifies, reviews, and approves. The agent is a tool in the
  human's workflow, not an autonomous actor.
- **Two `interrupt()` points** — `human_classify` and `human_approve` demonstrate multi-step human interaction, unlike
  the single `human_review` gate in other patterns.
- **Revision loop** — `human_approve` can route back to `agent` with specific feedback, demonstrating iterative
  human-guided refinement.
- **`MAX_ROUNDS` safety valve** prevents infinite revise loops.
- **Human instructions** allow the human to guide the agent's response style, tone, or content at the classification
  stage.
- **State carries human input** — `human_classification`, `human_instructions`, and `human_feedback` accumulate across
  the pipeline so downstream nodes can build on upstream decisions.

## Choosing a Pattern

### Decision Framework

Based on the article [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/),
most pattern decisions reduce to three questions:

1. **Is the workflow predictable?** If yes — sequential patterns win on cost and speed. If no — you need dynamic
   orchestration (coordinator, specialist, or event-driven).
2. **Does quality matter more than speed?** If yes — add reflection or human-in-the-loop for self-evaluation and
   oversight. If no — optimize for direct execution (ReAct, tool, sequential).
3. **Is the task genuinely complex?** If yes — consider planning (decomposition into ordered steps) or multi-agent
   collaboration. If no — start with a single agent and tool use.

### Trade-offs

| Pattern | Cost | Latency | Reliability | Observability | Best For |
|---------|------|---------|-------------|---------------|----------|
| **ReAct** | Medium | Medium | Medium | High | Adaptive problem-solving with tool use |
| **Reflection** | High | High | High | Medium | Quality-critical content generation |
| **Planning** | Medium | Medium | High | High | Multi-step tasks with dependencies |
| **Tool** | Low | Low | Medium | Medium | Single-shot external data/integration |
| **Coordinator** | Medium | Medium | Medium | High | Hub-and-spoke domain routing |
| **Specialist** | Medium | Medium | Medium | High | Peer-to-peer task delegation |
| **Event-Driven** | Medium | Medium | High | Low | Responsive cross-agent collaboration |
| **Sequential** | Low | Low | High | High | Fixed-order production pipelines |
| **Human-in-the-Loop** | Medium | High | High | Medium | High-stakes decisions requiring oversight |

### Pattern Selection Summary

- **Coordinator**: High-level workflow management. Use when tasks span multiple domains but need centralized routing.
- **Specialist**: Peer-to-peer delegation. Use when agents can self-determine the right handler.
- **Event-Driven**: Responsive collaboration. Use when agents need to react to events in real time.
- **ReAct**: Single-agent reasoning with tool calling. Use when external data or adaptive problem-solving is needed.
- **Reflection**: Iterative self-improvement through critique. Use when response quality matters more than speed.
- **Planning**: Structured step-by-step execution. Use for complex tasks that require ordered sub-steps with
  dependencies.
- **Tool**: Linear tool dispatch. Use when a single tool call resolves the query.
- **Sequential**: Fixed-order pipeline. Use for well-understood workflows with clear processing stages.
- **Human-in-the-Loop**: Human-driven classification and approval. Use when human judgment is critical to quality.

### Evolution Path

The expensive mistake is jumping to complex patterns prematurely. Start simple. Add complexity only when you encounter
clear limitations. Monitor costs, latency, and quality metrics. Let production feedback guide your decisions.

```
Single Agent + Tool  ──►  Reflection  ──►  Multi-Agent  ──►  Human-in-the-Loop
       ↓                    ↓                  ↓                  ↓
     ReAct              Quality            Complexity           Safety
```

Each pattern can evolve as requirements grow:

- **Sequential** workflows hit bottlenecks → add parallel processing or event-driven dispatch.
- **Single agents** max out capability → migrate to multi-agent systems (coordinator, specialist).
- **Pure automation** makes mistakes → insert human checkpoints (human-in-the-loop).
- **Direct execution** produces low-quality output → add reflection for self-critique.
- **Static routing** becomes inflexible → adopt event-driven pub-sub for dynamic dispatch.

## Enterprise Considerations

Based on the white paper [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/),
deploying multi-agent patterns in production requires addressing several architectural concerns:

### Stateful Processing

LangGraph's graph-based architecture maintains persistent context across interactions:
- **Checkpointing**: `MemorySaver` checkpoints state after every node execution, enabling recovery from failures without restarting workflows.
- **Interrupt/Resume**: The `interrupt()` / `Command(resume=...)` pattern pauses execution at human touchpoints and resumes from the exact paused state.
- **Thread isolation**: Each workflow run has a unique `thread_id`, preventing state leakage between concurrent executions.

### Modular Agent Architecture

Enterprise systems benefit from composing specialized agents rather than building monolithic LLM applications:
- **Single responsibility**: Each agent node handles exactly one domain or task (billing, technical, general).
- **Graph topology as architecture**: The graph structure (hub-and-spoke, mesh, pipeline) becomes the system's architectural diagram.
- **Pluggable nodes**: Adding a new capability means adding a node + edges without modifying existing agents.

### Dynamic Workflow Management

Patterns vary in how they handle conditional logic and branching:
- **Static routing** (Sequential, Tool): Fixed topology — fastest, simplest, least flexible.
- **Dynamic dispatch** (Coordinator, Specialist, Event-Driven): Agents or a hub decide the next node based on state — flexible but harder to reason about.
- **Adaptive loops** (ReAct, Reflection, Planning): Agents iterate based on intermediate results — most flexible, highest cost.

### Human-AI Collaboration

Every pattern in this module implements LangGraph's interrupt/resume mechanism:
- **Approval gates**: Human reviews proposed routing or agent output before it proceeds.
- **Redirect flows**: Humans can re-route misclassified queries back to the entry point.
- **Revision feedback**: In the Human-in-the-Loop pattern, humans provide specific guidance for agent revision.

### Production Checklist

| Concern | Implementation in this module | Production recommendation |
|---------|-------------------------------|--------------------------|
| **Checkpointing** | `MemorySaver` (in-memory) | PostgreSQL or Redis `Checkpointer` for durability |
| **Observability** | `@timed_node` decorator, `latencies` in state | LangSmith tracing for full execution visibility |
| **Error handling** | `MAX_ROUNDS` safety valve | Exponential backoff retries, dead-letter queues |
| **State persistence** | Python `Dict` in-memory | Pydantic models with serialization to database |
| **Human handoff** | `interrupt()` / `Command()` | Slack/email webhook notifications on interrupt |

## Resources

- [LangChain OpenTutorial — LangGraph Chatbot](https://langchain-opentutorial.gitbook.io/langchain-opentutorial/17-langgraph/01-core-features/02-langgraph-chatbot)
- [7 Must-Know Agentic AI Design Patterns](https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/) — Comprehensive guide to the seven core patterns covered in this module, including trade-off analysis and a decision framework
- [LangGraph: Architecting Advanced Multi-Agent Workflows for Enterprise AI Solutions](https://www.royalcyber.com/blogs/ai-ml/langgraph-multi-agent-workflows-enterprise-ai/) — Enterprise-focused white paper covering stateful processing, modular agent architecture, dynamic workflow management, and human-AI collaboration in production

## Course Modules

| Module | Topic | Preview | Labs |
|--------|-------|---------|------|
| 1 | LangGraph Architecture & Core Concepts | Build your first StateGraph workflows — a chatbot, an intent-classification agent, and a support-ticket routing system. Learn typed state, nodes, edges, and conditional routing fundamentals. | chatbot, customer_inquiry, tickets |
| 2 | Graph-Based State Management | Implement resilient document processing with error handling, retry logic, compliance tracking, and audit trails. Master state transitions, checkpointing, and failure recovery patterns. | legal_documents |
| 3 | Multi-Agent Systems | Explore 9 coordination strategies (coordinator, specialist, event-driven, ReAct, reflection, planning, tool, sequential, human-in-the-loop) applied to a unified support-ticket domain. Build a production-ready 5-agent research system with shared state, emergent intelligence, and circuit-breaker resilience. | 11 patterns + multi_agent_research |
| Agents | Tool-Calling Agents | Build LLM agents that call external tools — a cafe ordering assistant with menu/order/customer tools and a live weather forecast agent with HTTP integration. | cafe_agent, weather_agent |
