# LangGraph Framework — Coursera Course

This repository contains my work for the [LangGraph Framework](https://www.coursera.org/learn/langgraph-framework) course on Coursera.

## Overview

LangGraph is a framework for building stateful, multi-actor applications with Large Language Models (LLMs). It extends LangChain by adding the ability to define cyclic graphs, enabling agent loops, tool-calling, and complex multi-step reasoning workflows.

## Project Structure

```
src/langgraph_course/
├── config.py              # Shared configuration (API keys, model settings)
├── models.py              # Shared pydantic models / TypedDicts
├── utils/
│   ├── llm.py             # LLM client factory
│   └── graph.py           # Graph visualization / display helpers
├── module_1/              # Architecture & Core Concepts
│   └── labs/
├── module_2/              # State Management
│   └── labs/
└── module_3/              # Multi-Agent Systems
    └── labs/
tests/
├── base.py                # Shared TestCase with fixtures
├── test_module_1/
├── test_module_2/
└── test_module_3/
```

## Modules

| Module | Topic |
|--------|-------|
| 1 | Understanding LangGraph Architecture and Core Concepts |
| 2 | Implementing Graph-Based State Management |
| 3 | Building Multi-Agent Systems |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
poetry install
```

## Running Tests

```bash
poetry run python -m unittest discover -v
```
