from langchain.chat_models import init_chat_model

from langgraph_course.config import settings

from .base import BaseProvider, register_provider


@register_provider
class AutoDetectProvider(BaseProvider):
    name = "auto"

    def create_llm(
        self,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        return init_chat_model(
            model or settings.llm_model,
            temperature=temperature
            if temperature is not None
            else settings.llm_temperature,
        )
