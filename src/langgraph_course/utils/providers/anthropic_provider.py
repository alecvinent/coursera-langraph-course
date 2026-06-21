from langgraph_course.config import settings
from .base import BaseProvider, register_provider


@register_provider
class AnthropicProvider(BaseProvider):
    name = "anthropic"

    async def call(self, prompt: str) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.llm_api_key)
        resp = await client.messages.create(
            model=settings.llm_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text if resp.content else ""
