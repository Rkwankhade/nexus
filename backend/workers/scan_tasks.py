"""
Celery tasks for scan execution — dispatches recon/scanning tool wrappers
(nmap, nuclei, nikto, amass, etc.) as background jobs so the API layer can
return immediately and the frontend tracks progress over WebSocket.

Each task wraps an async tool-orchestrator call in asyncio.run() since
Celery workers execute tasks synchronously.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.scan import Scan, ScanStatus
from services.notification_service import notification_service
from utils.logger import get_logger

log = get_logger(__name__)


@shared_task(bind=True, name="workers.scan_tasks.run_scan_task", max_retries=1)
def run_scan_task(self, scan_id: str) -> dict[str, Any]:
    """Entry point invoked by routers/scans.py after creating a QUEUED Scan
    row. Runs the appropriate tool via tool_orchestrator and persists
    results back onto the Scan/Finding tables."""
    return asyncio.run(_run_scan_async(scan_id, self.request.id))


async def _run_scan_async(scan_id: str, celery_task_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan is None:
            log.error(f"scan_tasks: scan {scan_id} not found")
            return {"status": "failed", "error": "scan not found"}

        scan.status = ScanStatus.RUNNING
        scan.celery_task_id = celery_task_id
        scan.started_at = datetime.now(timezone.utc)
        await db.commit()

        await notification_service.push_job_progress(
            job_id=str(scan.id), user_id=str(scan.initiated_by), progress_pct=5, message="Scan started"
        )

        try:
            from services.tool_orchestrator import run_scan_tool

            def _on_progress(pct: int, message: str) -> None:
                # Fire-and-forget progress push from inside the orchestrator's
                # streaming callback; scheduled on the running loop.
                asyncio.get_event_loop().create_task(
                    notification_service.push_job_progress(
                        job_id=str(scan.id), user_id=str(scan.initiated_by), progress_pct=pct, message=message
                    )
                )

            tool_result = await run_scan_tool(
                tool_name=scan.tool,
                scan_type=scan.scan_type,
                parameters=scan.parameters,
                on_progress=_on_progress,
            )

            scan.raw_output = tool_result.get("raw_output", {})
            scan.progress_pct = 100
            scan.status = ScanStatus.COMPLETED if tool_result.get("succeeded") else ScanStatus.FAILED
            scan.finished_at = datetime.now(timezone.utc)
            await db.commit()

            await notification_service.push_job_completed(
                job_id=str(scan.id),
                user_id=str(scan.initiated_by),
                status=scan.status.value,
                summary={"findings_created": tool_result.get("findings_created", 0)},
            )

            return {"status": scan.status.value, "findings_created": tool_result.get("findings_created", 0)}

        except Exception as exc:
            log.error(f"scan_tasks: scan {scan_id} failed: {exc}")
            scan.status = ScanStatus.FAILED
            scan.finished_at = datetime.now(timezone.utc)
            scan.raw_output = {"error": str(exc)}
            await db.commit()

            await notification_service.push_job_completed(
                job_id=str(scan.id), user_id=str(scan.initiated_by), status="failed", summary={"error": str(exc)}
            )
            return {"status": "failed", "error": str(exc)}


@shared_task(name="workers.scan_tasks.cancel_scan_task")
def cancel_scan_task(scan_id: str) -> dict[str, Any]:
    return asyncio.run(_cancel_scan_async(scan_id))


async def _cancel_scan_async(scan_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan is None:
            return {"status": "failed", "error": "scan not found"}
        if scan.status in (ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED):
            return {"status": scan.status.value, "message": "scan already finished"}

        scan.status = ScanStatus.CANCELLED
        scan.finished_at = datetime.now(timezone.utc)
        await db.commit()

        if scan.celery_task_id:
            from workers.celery_app import celery_app

            celery_app.control.revoke(scan.celery_task_id, terminate=True)

        return {"status": "cancelled"}
