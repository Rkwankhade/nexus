import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from models.tool_job import ToolCategory, ToolJobStatus


class ToolJobCreate(BaseModel):
    target_id: Optional[uuid.UUID] = None
    category: ToolCategory
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: Optional[uuid.UUID] = None
    requested_by: uuid.UUID
    category: ToolCategory
    tool_name: str
    command: str
    status: ToolJobStatus
    stdout_log: str
    stderr_log: str
    parsed_output: Dict[str, Any]
    exit_code: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
