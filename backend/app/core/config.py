from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration (reads backend/.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_anon_key: str = ""
    # Server-side only; unused until Phase 3. Never returned by any endpoint.
    supabase_service_role_key: str = Field(default="", repr=False)

    cors_origins: str = "http://localhost:5173"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3-vl:4b"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
