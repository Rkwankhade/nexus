import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ScanType(str, enum.Enum):
    RECON = "recon"
    PORT_SCAN = "port_scan"
    VULN_SCAN = "vuln_scan"
    WEB_SCAN = "web_scan"
    WIRELESS_SCAN = "wireless_scan"


class ScanStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus, values_callable=lambda obj: [e.value for e in obj]), default=ScanStatus.QUEUED)
    celery_task_id: Mapped[str] = mapped_column(String(64), nullable=True)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    raw_output: Mapped[dict] = mapped_column(JSONB, default=dict)
    progress_pct: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

