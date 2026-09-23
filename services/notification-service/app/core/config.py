from functools import lru_cache
from pydantic import Field
from sigtpi_common.utils.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "notification-service"
    smtp_host: str = Field("mailhog", alias="SMTP_HOST")
    smtp_port: int = Field(1025, alias="SMTP_PORT")
    smtp_from: str = Field("noreply@sigtpi.local", alias="SMTP_FROM_EMAIL")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
