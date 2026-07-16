from langchain_openai import ChatOpenAI
from config import settings
from .base import BaseProvider, register_provider


@register_provider
class OpenRouterProvider(BaseProvider):
    name = "openrouter"

    def create_llm(
        self,
        model: str | None = None,
        temperature: float | None = None,
    ) -> ChatOpenAI:
        self.validate_config()
        return ChatOpenAI(
            model=model or settings.llm_model,
            temperature=temperature
            if temperature is not None
            else settings.llm_temperature,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

    async def call(self, prompt: str) -> str:
        self.validate_config()
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        resp = await client.chat.completions.create(
            model=settings.ai_model or settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.llm_temperature,
        )
        return resp.choices[0].message.content or ""

    def validate_config(self) -> None:
        missing = []
        if not settings.openrouter_api_key:
            missing.append("openrouter_api_key")
        if not settings.openrouter_base_url:
            missing.append("openrouter_base_url")
        if missing:
            raise ValueError(
                f"OpenRouter provider requires: {', '.join(missing)}. "
                "Set them in .env or export the environment variables."
            )
