"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    app_name: str = "Transaction API"
    app_version: str = "0.1.0"
    debug: bool = False

    log_level: str = "INFO"
    log_dir: str = "logs"

    host: str = "0.0.0.0"
    port: int = 8000

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "transaction_db"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_echo: bool = False

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}" f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    def redis_url(self) -> str:
        """Construct Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
