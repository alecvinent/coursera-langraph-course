from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
    }

    llm_provider: str = "auto"
    llm_model: str = ''
    ai_model: str = ''
    llm_temperature: float = Field(default=0.3)
    llm_api_key: str = ''
    openrouter_api_key: str = ''
    openrouter_base_url: str = "https://openrouter.ai/api/v1"


settings = Settings()
