# LangGraph Framework — Coursera Course

Workbook for the [LangGraph Framework](https://www.coursera.org/learn/langgraph-framework) course on Coursera.

## Overview

LangGraph is a framework for building stateful, multi-actor applications with Large Language Models (LLMs). It extends LangChain by adding the ability to define cyclic graphs, enabling agent loops, tool-calling, and complex multi-step reasoning workflows.

> AI coding assistants working on this repo should read [`AGENTS.md`](AGENTS.md) for conventions, testing setup, and agent behavior guidelines.

## Project Structure

```
src/langgraph_course/
├── config.py                # Shared configuration (API keys, model settings)
├── models.py                # Shared TypedDicts / Pydantic models
├── log.py                   # Loguru configuration
├── utils/
│   ├── llm.py               # LLMFactory — sync (LangChain) and async (direct SDK)
│   ├── graph.py             # Graph visualization helpers
│   └── providers/           # Provider registry for LLM backends
│       ├── base.py          #   BaseProvider ABC + register_provider
│       ├── openrouter.py    #   OpenRouter (AsyncOpenAI)
│       ├── openai_provider.py   #   OpenAI (AsyncOpenAI)
│       └── anthropic_provider.py # Anthropic (AsyncAnthropic)
├── module_1/                # Understanding LangGraph Architecture
│   └── labs/                # Exercises for Module 1
├── module_2/                # Implementing State Management
│   └── labs/                # Exercises for Module 2
└── module_3/                # Building Multi-Agent Systems
    └── labs/                # Exercises for Module 3
├── agents/                  # Tool-calling agents
│   ├── models.py            # Pydantic models (Customer, Order, MenuOptions, etc.)
│   ├── tools.py             # Tool functions (get_daily_menu, create_order, etc.)
│   ├── prompts.py           # System prompts for agent behavior
│   └── cafe_agent.py        # 2-node LangGraph tool-calling graph
tests/
├── base.py                  # Shared TestCase with setUp/tearDown helpers
├── test_module_1/           # Tests for Module 1 exercises
├── test_module_2/           # Tests for Module 2 exercises
├── test_module_3/           # Tests for Module 3 exercises
└── test_agents/             # Tests for tool-calling agents
```

## How to Work on an Exercise

Each module has a `labs/` directory with exercise files. Each exercise follows this pattern:

1. **Scaffold** — the exercise file (`module_X/labs/exercise_name.py`) provides stub functions with type signatures and docstrings.
2. **Tests** — the matching test file (`tests/test_module_X/test_exercise_name.py`) defines what each function should do.
3. **Implement** — fill in the function bodies in the exercise file.
4. **Verify** — run the tests to check your implementation.

```bash
# Run tests for a specific exercise
poetry run python -m unittest tests.test_module_1.test_customer_inquiry -v

# Run all tests
poetry run python -m unittest discover -v
```

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

| Provider | `llm_provider` | Required env vars |
|---|---|---|
| OpenRouter | `"openrouter"` | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` |
| OpenAI | `"openai"` | `LLM_API_KEY` |
| Anthropic | `"anthropic"` | `LLM_API_KEY` |

The `config.py` loader reads these automatically at import time.

## Calling a Provider

Use `LLMFactory.call()` to make an async LLM call — it dispatches to the correct provider based on `settings.llm_provider`:

```python
import asyncio
from langgraph_course.utils.llm import LLMFactory

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
from langgraph_course.utils.providers.openrouter import OpenRouterProvider

provider = OpenRouterProvider()
response = asyncio.run(provider.call("Hello"))
```

## Running Tests

```bash
# Run all tests
poetry run python -m unittest discover -v

# Run tests for a specific module
poetry run python -m unittest tests.test_module_1 -v

# Run tests for a specific exercise
poetry run python -m unittest tests.test_module_1.test_customer_inquiry -v
```

## Resources

- [LangChain OpenTutorial — LangGraph Chatbot](https://langchain-opentutorial.gitbook.io/langchain-opentutorial/17-langgraph/01-core-features/02-langgraph-chatbot)

## Course Modules

| Module | Topic | Labs |
|--------|-------|------|
| 1 | Understanding LangGraph Architecture and Core Concepts | customer_inquiry |
| 2 | Implementing Graph-Based State Management | — |
| 3 | Building Multi-Agent Systems | — |
| Agents | Tool-calling agents with LLM graphs | cafe_agent |
