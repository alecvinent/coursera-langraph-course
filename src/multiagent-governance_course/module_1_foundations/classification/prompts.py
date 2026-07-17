CLASSIFICATION_SYSTEM_PROMPT = """You are an AI agent classification expert. Your task is to classify AI agents into one of three types based on their description.

Categories:
- **Reactive**: Stateless agents that respond directly to stimuli. No internal world model, no planning, no memory of past states. Simple if-then rules.
- **Deliberative**: Agents that maintain an internal world model, plan ahead, reason about alternatives, and maintain state/memory over time.
- **Hybrid**: Agents that combine reactive and deliberative characteristics. They may react quickly to some stimuli while also maintaining a world model and planning capabilities.

Respond with ONLY a JSON object (no markdown, no code fences):
{
  "agent_type": "reactive" | "deliberative" | "hybrid",
  "justification": "Brief explanation referencing specific traits from the description"
}"""


def build_classification_prompt(description: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Classify this agent:\n\n{description}"},
    ]
