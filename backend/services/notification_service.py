"""
Notification service — bridges backend events (tool job progress, scan
completion, new alerts) to connected browser clients over WebSocket, using
Redis pub/sub as the transport so any worker process (Celery included) can
publish without holding a direct WebSocket reference.

routers/websocket.py subscribes to the per-user/per-job channels this
module publishes to and forwards messages to the browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from core.redis_client import redis_client
from utils.logger import get_logger

log = get_logger(__name__)


class NotificationType(str, Enum):
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    SCAN_STATUS = "scan_status"
    NEW_FINDING = "new_finding"
    NEW_ALERT = "new_alert"
    REPORT_READY = "report_ready"
    AI_ANALYSIS_READY = "ai_analysis_ready"


@dataclass
class Notification:
    type: NotificationType
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type.value, "payload": self.payload, "timestamp": self.timestamp}


def _user_channel(user_id: str) -> str:
    return f"nexus:notifications:user:{user_id}"


def _job_channel(job_id: str) -> str:
    return f"nexus:notifications:job:{job_id}"


def _broadcast_channel() -> str:
    return "nexus:notifications:broadcast"


class NotificationService:
    async def notify_user(self, user_id: str, notification: Notification) -> None:
        await redis_client.publish_json(_user_channel(user_id), notification.to_dict())

    async def notify_job_subscribers(self, job_id: str, notification: Notification) -> None:
        """Used for the live output terminal — anyone watching a specific
        tool_job/scan gets streamed updates regardless of who launched it."""
        await redis_client.publish_json(_job_channel(job_id), notification.to_dict())

    async def broadcast(self, notification: Notification) -> None:
        """Platform-wide notices (e.g. a new critical alert visible to the
        whole SOC team, not just the initiating user)."""
        await redis_client.publish_json(_broadcast_channel(), notification.to_dict())

    async def push_job_progress(self, job_id: str, user_id: str, progress_pct: int, message: str = "") -> None:
        notification = Notification(
            type=NotificationType.JOB_PROGRESS,
            payload={"job_id": job_id, "progress_pct": progress_pct, "message": message},
        )
        await self.notify_job_subscribers(job_id, notification)
        await self.notify_user(user_id, notification)

    async def push_job_completed(self, job_id: str, user_id: str, status: str, summary: Optional[dict] = None) -> None:
        notification = Notification(
            type=NotificationType.JOB_COMPLETED if status == "completed" else NotificationType.JOB_FAILED,
            payload={"job_id": job_id, "status": status, "summary": summary or {}},
        )
        await self.notify_job_subscribers(job_id, notification)
        await self.notify_user(user_id, notification)

    async def push_new_finding(self, user_id: str, finding_id: str, target_id: str, severity: str, title: str) -> None:
        notification = Notification(
            type=NotificationType.NEW_FINDING,
            payload={"finding_id": finding_id, "target_id": target_id, "severity": severity, "title": title},
        )
        await self.notify_user(user_id, notification)
        if severity in ("critical", "high"):
            await self.broadcast(notification)

    async def push_new_alert(self, alert_id: str, severity: str, title: str) -> None:
        notification = Notification(
            type=NotificationType.NEW_ALERT,
            payload={"alert_id": alert_id, "severity": severity, "title": title},
        )
        await self.broadcast(notification)

    async def push_report_ready(self, user_id: str, report_id: str, file_path: str) -> None:
        notification = Notification(
            type=NotificationType.REPORT_READY,
            payload={"report_id": report_id, "file_path": file_path},
        )
        await self.notify_user(user_id, notification)

    def stream_output_line(self, job_id: str, user_id: str):
        """Returns a synchronous callback compatible with tools.base.run_command's
        `on_output_line` param — used by tool_orchestrator to stream live
        stdout lines to the frontend terminal (xterm.js) as a job runs.
        Wraps the async publish in a fire-and-forget task since run_command's
        callback is invoked from a sync context inside the read loop."""
        import asyncio

        def _callback(line: str) -> None:
            notification = Notification(
                type=NotificationType.JOB_PROGRESS,
                payload={"job_id": job_id, "output_line": line},
            )
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.notify_job_subscribers(job_id, notification))
            except RuntimeError:
                log.warning("no running event loop; dropping live output line notification")

        return _callback


notification_service = NotificationService()
