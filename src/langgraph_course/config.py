from dotenv import load_dotenv

load_dotenv()

# Model settings — override via .env or environment
LLM_MODEL: str = "gpt-4o-mini"
LLM_TEMPERATURE: float = 0.0
LLM_MAX_TOKENS: int | None = None
