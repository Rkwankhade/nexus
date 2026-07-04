import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class LogSource(str, enum.Enum):
    SURICATA = "suricata"
    WAZUH = "wazuh"
    SYSLOG = "syslog"
    FIREWALL = "firewall"
    AUTH = "auth"
    CUSTOM = "custom"


class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[LogSource] = mapped_column(Enum(LogSource, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    host: Mapped[str] = mapped_column(String(255), default="")
    event_type: Mapped[str] = mapped_column(String(128), default="")
    severity: Mapped[str] = mapped_column(String(32), default="info")
    message: Mapped[str] = mapped_column(String(2048), default="")
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)
    matched_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

