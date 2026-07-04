import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ToolCategory(str, enum.Enum):
    RECON = "recon"
    SCANNING = "scanning"
    WEB = "web"
    EXPLOITATION = "exploitation"
    PASSWORD = "password"
    POST_EXPLOIT = "post_exploit"
    NETWORK = "network"
    WIRELESS = "wireless"
    BLUETEAM = "blueteam"
    FORENSICS = "forensics"


class ToolJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ToolJob(Base):
    """
    Unified record for every subprocess/API-driven tool execution
    (nmap, sqlmap, hashcat, volatility, etc). Scan and ExploitAttempt
    reference specific higher-level workflows; ToolJob is the raw
    execution ledger used by the orchestrator and live terminal feed.
    """
    __tablename__ = "tool_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("targets.id"), nullable=True
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    category: Mapped[ToolCategory] = mapped_column(Enum(ToolCategory, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    command: Mapped[str] = mapped_column(String(2048), default="")
    status: Mapped[ToolJobStatus] = mapped_column(
        Enum(ToolJobStatus, values_callable=lambda obj: [e.value for e in obj]), default=ToolJobStatus.QUEUED
    )
    celery_task_id: Mapped[str] = mapped_column(String(64), nullable=True)
    stdout_log: Mapped[str] = mapped_column(String, default="")
    stderr_log: Mapped[str] = mapped_column(String, default="")
    parsed_output: Mapped[dict] = mapped_column(JSONB, default=dict)
    exit_code: Mapped[int] = mapped_column(nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

