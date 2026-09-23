"""Service-specific configuration extending BaseServiceSettings."""
from functools import lru_cache
from sigtpi_common.utils.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "auth-service"
    # search_path is set at the postgres role level via init.sql
    # No URL override needed


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
