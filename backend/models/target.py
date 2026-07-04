import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TargetType(str, enum.Enum):
    DOMAIN = "domain"
    IP = "ip"
    IP_RANGE = "ip_range"
    URL = "url"
    WIRELESS_SSID = "wireless_ssid"


class TargetStatus(str, enum.Enum):
    PENDING_AUTH = "pending_auth"
    AUTHORIZED = "authorized"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Target(Base):
    """
    Represents an authorized engagement scope item. Every scan/exploit
    action must reference a Target whose status is AUTHORIZED or ACTIVE
    and whose authorization_document is on file — enforced at the
    service layer, not just here.
    """
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    type: Mapped[TargetType] = mapped_column(
        Enum(TargetType, name="targettype", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Mapped[TargetStatus] = mapped_column(
        Enum(TargetStatus, name="targetstatus", values_callable=lambda obj: [e.value for e in obj]),
        default=TargetStatus.PENDING_AUTH,
    )
    description: Mapped[str] = mapped_column(Text, default="")
    authorization_reference: Mapped[str] = mapped_column(
        String(255), default="", doc="Ticket/contract ref proving written authorization"
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

