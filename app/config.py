from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    api_port: int = 8081
    app_env: str = "development"
    log_level: str = "info"
    secret_key: str = "change-me-to-a-random-string"
    algorithm: str = "HS256"
    imap_default_port: int = 993
    imap_timeout_seconds: int = 15
    verification_lookback_minutes: int = 15
    verification_max_messages: int = 20
    secret_encryption_key: str = "change-me-to-a-random-string"
    redaction_enabled: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
