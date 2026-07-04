import uuid
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict

from models.alert import AlertSeverity, AlertStatus


class AlertUpdate(BaseModel):
    status: AlertStatus


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    source: str
    rule_id: str
    mitre_techniques: Dict[str, Any]
    created_at: datetime
