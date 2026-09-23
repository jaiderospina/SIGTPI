from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TimestampedSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime

class IdentifiedSchema(TimestampedSchema):
    id: UUID

class PaginatedResponse(BaseSchema):
    total: int; page: int; page_size: int; items: list

class HealthResponse(BaseSchema):
    status: str; service: str; version: str; environment: str
