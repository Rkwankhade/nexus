import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    REMEDIATED = "remediated"
    ACCEPTED_RISK = "accepted_risk"


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[Severity] = mapped_column(Enum(Severity, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, values_callable=lambda obj: [e.value for e in obj]), default=FindingStatus.OPEN
    )
    cvss_score: Mapped[float] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[str] = mapped_column(String(128), nullable=True)
    cve_ids: Mapped[list] = mapped_column(ARRAY(String), default=list)
    mitre_techniques: Mapped[list] = mapped_column(ARRAY(String), default=list)
    affected_host: Mapped[str] = mapped_column(String(255), default="")
    affected_port: Mapped[int] = mapped_column(nullable=True)
    affected_service: Mapped[str] = mapped_column(String(128), default="")
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    remediation: Mapped[str] = mapped_column(Text, default="")
    source_tool: Mapped[str] = mapped_column(String(64), default="")
    ai_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

