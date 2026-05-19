from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440  # 24 hours
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-4-6"

    model_config = {"env_prefix": "BGA_"}


settings = Settings()
