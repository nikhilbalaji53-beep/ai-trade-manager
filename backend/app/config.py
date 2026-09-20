from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TradePilot — AI-Powered Real-Time NSE/BSE Trading System"
    api_prefix: str = "/api"
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )
    starting_capital: float = 500_000.0
    environment: str = "production"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 2
    secret_key: str = "tradepilot-production-secret-key-change-in-env"
    gzip_minimum_size: int = 1000
    market_data_provider: str = "NSE_LIVE"
    market_data_mode: str = "live"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    @property
    def is_debug(self) -> bool:
        return self.debug and not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()
