import functools
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).resolve().parents[3] / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    REDIS_URL: str

    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, gt=0)
    ASK_RATE_LIMIT: int = Field(default=5, gt=0)
    UPLOAD_RATE_LIMIT: int = Field(default=3, gt=0)
    LOGIN_RATE_LIMIT: int = Field(default=10, gt=0)
    REGISTER_RATE_LIMIT: int = Field(default=5, gt=0)

    JWT_SECRET_KEY: SecretStr = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024

    OLLAMA_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:3b"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()
