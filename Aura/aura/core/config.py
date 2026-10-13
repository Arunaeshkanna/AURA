from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AURA"
    env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    vector_dir: Path = Path("./aura/data/vectorstore")
    docs_dir: Path = Path("./aura/data/documents")
    reports_dir: Path = Path("./aura/data/reports")
    memory_dir: Path = Path("./aura/data/memory")
    metrics_dir: Path = Path("./aura/data/metrics")
    router_model_path: Path = Path("./aura/data/router/router.joblib")
    fast_model: str = "openai/gpt-oss-20b"
    powerful_model: str = "openai/gpt-oss-120b"
    small_model: str = "openai/gpt-oss-20b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_prompt_tokens: int = 6_000
    use_chroma: bool = True
    chroma_host: str | None = None
    chroma_port: int = 8001
    use_langgraph: bool = True
    distributed_agents: bool = False
    agent_base_url: str = "http://127.0.0.1:8100"
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AURA_",
        extra="ignore",
    )

    def ensure_dirs(self) -> None:
        for path in [
            self.vector_dir,
            self.docs_dir,
            self.reports_dir,
            self.memory_dir,
            self.metrics_dir,
            self.router_model_path.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
