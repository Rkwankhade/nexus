import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from models.scan import ScanStatus, ScanType


class ScanCreate(BaseModel):
    target_id: uuid.UUID
    scan_type: ScanType
    tool: str
    parameters: Dict[str, Any] = {}


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    initiated_by: uuid.UUID
    scan_type: ScanType
    tool: str
    status: ScanStatus
    progress_pct: int
    parameters: Dict[str, Any]
    raw_output: Dict[str, Any]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
