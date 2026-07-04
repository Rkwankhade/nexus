import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from models.target import TargetStatus, TargetType


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1, max_length=512)
    type: TargetType
    description: str = ""
    authorization_reference: str = Field(
        default="",
        description="Required proof of written authorization (ticket/contract ref)",
    )


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TargetStatus] = None
    authorization_reference: Optional[str] = None


class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    value: str
    type: TargetType
    status: TargetStatus
    description: str
    authorization_reference: str
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
