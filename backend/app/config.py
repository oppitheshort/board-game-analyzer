import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440  # 24 hours
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-4-6"
    environment: str = "production"  # "development" or "production"
    ws_max_message_bytes: int = 65536  # 64KB max WebSocket message

    model_config = {"env_prefix": "BGA_"}


settings = Settings()

# If no JWT secret is set, generate a random one (persists for this process only).
# In production, ALWAYS set BGA_JWT_SECRET as an environment variable.
if not settings.jwt_secret:
    settings.jwt_secret = secrets.token_urlsafe(48)
