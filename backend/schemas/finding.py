import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from models.finding import FindingStatus, Severity


class FindingCreate(BaseModel):
    target_id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    title: str
    description: str = ""
    severity: Severity
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cve_ids: List[str] = []
    mitre_techniques: List[str] = []
    affected_host: str = ""
    affected_port: Optional[int] = None
    affected_service: str = ""
    evidence: Dict[str, Any] = {}
    remediation: str = ""
    source_tool: str = ""


class FindingUpdate(BaseModel):
    status: Optional[FindingStatus] = None
    remediation: Optional[str] = None
    severity: Optional[Severity] = None


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    title: str
    description: str
    severity: Severity
    status: FindingStatus
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cve_ids: List[str]
    mitre_techniques: List[str]
    affected_host: str
    affected_port: Optional[int] = None
    affected_service: str
    evidence: Dict[str, Any]
    remediation: str
    source_tool: str
    ai_analysis: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
