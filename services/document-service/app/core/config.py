from functools import lru_cache
from pydantic import Field
from sigtpi_common.utils.settings import BaseServiceSettings


class Settings(BaseServiceSettings):
    service_name: str = "document-service"
    file_storage_path: str = Field("/app/storage", alias="FILE_STORAGE_PATH")
    max_upload_size_mb: int = Field(50, alias="MAX_UPLOAD_SIZE_MB")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
