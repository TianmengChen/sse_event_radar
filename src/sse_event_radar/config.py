from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "sse-event-radar"
    app_env: str = "dev"
    log_level: str = "INFO"

    proxy_enabled: bool = False
    proxy_url: str | None = None
    no_proxy: str = "localhost,127.0.0.1,::1"

    data_dir: Path = Path("./data")
    database_url: str = "sqlite:///./data/db/sse_event_radar.sqlite3"

    quote_poll_seconds: int = 60
    announcement_poll_minutes: int = 5
    stock_master_refresh_hour: int = 17

    akshare_rate_limit_seconds: int = 3

    enable_llm: bool = False
    openai_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"

    enable_telegram: bool = False
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
