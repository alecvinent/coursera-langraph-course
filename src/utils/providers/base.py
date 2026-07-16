from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel

_PROVIDERS: dict[str, type["BaseProvider"]] = {}


def register_provider(cls: type["BaseProvider"]) -> type["BaseProvider"]:
    _PROVIDERS[cls.name] = cls
    return cls


def get_provider(name: str) -> type["BaseProvider"]:
    if name not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider {name!r}. "
            f"Available: {list(_PROVIDERS)}"
        )
    return _PROVIDERS[name]


class BaseProvider(ABC):
    name: str = ""

    async def call(self, prompt: str) -> str:
        """Call the LLM with a prompt and return the response text."""
        raise NotImplementedError

    def create_llm(
        self,
        model: str | None = None,
        temperature: float | None = None,
    ) -> BaseChatModel:
        raise NotImplementedError

    def validate_config(self) -> None:
        return None
