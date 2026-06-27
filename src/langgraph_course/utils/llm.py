import random

from langchain_core.language_models import BaseChatModel

from langgraph_course.config import settings
from .providers import get_provider
from langgraph_course.log import logger

ENABLED_MODELS = [
    'openai/gpt-oss-120b:free',
    'cohere/north-mini-code:free',
    # 'nvidia/llama-nemotron-rerank-vl-1b-v2:free',
    # 'nvidia/nemotron-3-ultra-550b-a55b:free',
    # 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    'poolside/laguna-xs.2:free',
    # 'poolside/laguna-m.1:free',
    'google/gemma-4-26b-a4b-it:free',
    'qwen/qwen3-next-80b-a3b-instruct:free',
    'cognitivecomputations/dolphin-mistral-24b-venice-edition:free',
    'meta-llama/llama-3.3-70b-instruct:free'
]


class LLMFactory:
    _cache: dict[str, BaseChatModel] = {}

    @classmethod
    def create(
            cls,
            provider: str | None = None,
            model: str | None = None,
            temperature: float | None = None,
    ) -> BaseChatModel:
        provider_name = provider or settings.llm_provider
        provider_cls = get_provider(provider_name)
        instance = provider_cls()
        instance.validate_config()

        if not model:
            model = random.choice(ENABLED_MODELS)

        logger.info(f"Using model: {model}")

        return instance.create_llm(model, temperature)

    @classmethod
    async def call(
            cls,
            prompt: str,
            provider: str | None = None,
    ) -> str:
        provider_name = provider or settings.llm_provider
        provider_cls = get_provider(provider_name)
        instance = provider_cls()
        instance.validate_config()
        return await instance.call(prompt)

    @classmethod
    def cached(
            cls,
            provider: str | None = None,
            model: str | None = None,
            temperature: float | None = None,
    ) -> BaseChatModel:
        resolved_provider = provider or settings.llm_provider
        resolved_model = model or settings.llm_model
        key = f"{resolved_provider}:{resolved_model}"
        if key not in cls._cache:
            cls._cache[key] = cls.create(resolved_provider, resolved_model, temperature)
        return cls._cache[key]

    @staticmethod
    def default(
            model: str | None = None,
            temperature: float | None = None,
    ) -> BaseChatModel:
        return LLMFactory.create(model=model, temperature=temperature)

    @staticmethod
    def openrouter(
            model: str | None = None,
            temperature: float | None = None,
    ) -> BaseChatModel:
        return LLMFactory.create(
            provider="openrouter", model=model, temperature=temperature
        )


get_llm = LLMFactory.default
get_openrouter_llm = LLMFactory.openrouter
