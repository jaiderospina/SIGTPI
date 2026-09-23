from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        # Allow pydantic-settings to parse JSON strings for list fields
        env_parse_none_str="null",
    )

    environment: str = Field("development", alias="ENVIRONMENT")
    debug: bool = Field(False, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    service_name: str = "sigtpi-service"

    postgres_host: str = Field("postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    postgres_user: str = Field("sigtpi", alias="POSTGRES_USER")
    postgres_password: str = Field("sigtpi_dev", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("sigtpi", alias="POSTGRES_DB")

    redis_host: str = Field("redis", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_password: str = Field("", alias="REDIS_PASSWORD")
    redis_db: int = Field(0, alias="REDIS_DB")

    rabbitmq_host: str = Field("rabbitmq", alias="RABBITMQ_HOST")
    rabbitmq_port: int = Field(5672, alias="RABBITMQ_PORT")
    rabbitmq_user: str = Field("sigtpi", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field("sigtpi_dev", alias="RABBITMQ_PASSWORD")
    rabbitmq_vhost: str = Field("sigtpi", alias="RABBITMQ_VHOST")

    jwt_secret_key: str = Field(
        "dev_secret_change_in_prod_min32chars!!",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(480, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # cors_origins stored as plain string, parsed in property
    cors_origins_raw: str = Field(
        "http://localhost:3000,http://localhost:8080",
        alias="CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> list[str]:
        v = self.cors_origins_raw.strip()
        if v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        """Plain asyncpg URL — search_path set via connect_args in database.py."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )
