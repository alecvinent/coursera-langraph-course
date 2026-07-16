from config import settings
from .base import BaseProvider, register_provider


@register_provider
class OpenAIProvider(BaseProvider):
    name = "openai"

    async def call(self, prompt: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.llm_api_key)
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.llm_temperature,
        )
        return resp.choices[0].message.content or ""
