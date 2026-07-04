import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict

from models.report import ReportFormat, ReportStatus


class ReportCreate(BaseModel):
    target_id: uuid.UUID
    title: str
    format: ReportFormat = ReportFormat.PDF
    finding_ids: List[uuid.UUID] = []


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    generated_by: uuid.UUID
    title: str
    format: ReportFormat
    status: ReportStatus
    file_path: str | None = None
    summary: Dict[str, Any]
    created_at: datetime
