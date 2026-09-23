"""Service-specific configuration extending BaseServiceSettings."""
from functools import lru_cache
from sigtpi_common.utils.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "academic-registry"
    # Add service-specific settings below
    # example_setting: str = Field("default", alias="EXAMPLE_SETTING")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
