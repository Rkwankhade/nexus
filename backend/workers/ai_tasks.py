"""
Celery tasks for AI analysis that's too slow/bulky to run inline on an API
request — e.g. bulk finding triage after a large scan completes, or
regenerating a target's posture summary after many findings changed.
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery import shared_task
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.finding import Finding
from models.target import Target
from services.notification_service import notification_service
from utils.logger import get_logger

log = get_logger(__name__)


@shared_task(name="workers.ai_tasks.analyze_findings_bulk_task")
def analyze_findings_bulk_task(finding_ids: list[str], user_id: str) -> dict[str, Any]:
    """Run AI triage analysis across a batch of findings (e.g. all findings
    produced by a single completed scan) and persist results."""
    return asyncio.run(_analyze_findings_bulk_async(finding_ids, user_id))


async def _analyze_findings_bulk_async(finding_ids: list[str], user_id: str) -> dict[str, Any]:
    from services.ai_engine import ai_engine

    analyzed, failed = 0, 0

    async with AsyncSessionLocal() as db:
        for finding_id in finding_ids:
            result = await db.execute(select(Finding).where(Finding.id == finding_id))
            finding = result.scalar_one_or_none()
            if finding is None:
                failed += 1
                continue
            try:
                analysis = await ai_engine.analyze_finding(finding)
                finding.ai_analysis = analysis
                await db.commit()
                analyzed += 1

                await notification_service.notify_user(
                    user_id,
                    notification=_ai_ready_notification(str(finding.id)),
                )
            except Exception as exc:
                log.warning(f"ai_tasks: analysis failed for finding {finding_id}: {exc}")
                await db.rollback()
                failed += 1

    return {"analyzed": analyzed, "failed": failed, "total": len(finding_ids)}


@shared_task(name="workers.ai_tasks.refresh_target_posture_task")
def refresh_target_posture_task(target_id: str, user_id: str) -> dict[str, Any]:
    return asyncio.run(_refresh_target_posture_async(target_id, user_id))


async def _refresh_target_posture_async(target_id: str, user_id: str) -> dict[str, Any]:
    from services.ai_engine import ai_engine

    async with AsyncSessionLocal() as db:
        target_result = await db.execute(select(Target).where(Target.id == target_id))
        target = target_result.scalar_one_or_none()
        if target is None:
            return {"status": "failed", "error": "target not found"}

        findings_result = await db.execute(select(Finding).where(Finding.target_id == target_id))
        findings = findings_result.scalars().all()

        try:
            summary = await ai_engine.summarize_target_posture(target, findings)
        except Exception as exc:
            log.error(f"ai_tasks: posture refresh failed for target {target_id}: {exc}")
            return {"status": "failed", "error": str(exc)}

        await notification_service.notify_user(user_id, notification=_ai_ready_notification(str(target.id)))
        return {"status": "completed", "summary": summary}


def _ai_ready_notification(subject_id: str):
    from services.notification_service import Notification, NotificationType

    return Notification(type=NotificationType.AI_ANALYSIS_READY, payload={"subject_id": subject_id})
