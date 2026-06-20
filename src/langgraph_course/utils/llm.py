from langchain.chat_models import init_chat_model

from langgraph_course.config import LLM_MODEL, LLM_TEMPERATURE


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
) -> ChatModel:
    return init_chat_model(
        model or LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
    )
