# config.py — Environment loading via pydantic-settings
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODEL: str = "qwen/qwen3-32b"

    HINDSIGHT_BASE_URL: str = ""
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_BANK_ID: str = "dejavu-eng"

    TTS_PROVIDER: str = "groq"  # "groq" | "browser"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
