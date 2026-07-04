"""
Celery task for report generation — assembling a PDF is fast for small
targets but can take real time for a target with hundreds of findings and
an AI-generated summary, so it runs off the request thread.
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery import shared_task
from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.finding import Finding
from models.report import Report, ReportStatus
from models.target import Target
from services.notification_service import notification_service
from utils.logger import get_logger

log = get_logger(__name__)


@shared_task(name="workers.report_tasks.generate_report_task")
def generate_report_task(report_id: str) -> dict[str, Any]:
    return asyncio.run(_generate_report_async(report_id))


async def _generate_report_async(report_id: str) -> dict[str, Any]:
    from schemas.finding import FindingOut
    from services.ai_engine import ai_engine
    from services.report_generator import ReportGenerationError, build_report

    async with AsyncSessionLocal() as db:
        report_result = await db.execute(select(Report).where(Report.id == report_id))
        report = report_result.scalar_one_or_none()
        if report is None:
            log.error(f"report_tasks: report {report_id} not found")
            return {"status": "failed", "error": "report not found"}

        target_result = await db.execute(select(Target).where(Target.id == report.target_id))
        target = target_result.scalar_one_or_none()
        if target is None:
            report.status = ReportStatus.FAILED
            await db.commit()
            return {"status": "failed", "error": "target not found"}

        findings_result = await db.execute(select(Finding).where(Finding.target_id == report.target_id))
        findings = findings_result.scalars().all()
        finding_dicts = [FindingOut.model_validate(f).model_dump(mode="json") for f in findings]

        ai_summary = None
        try:
            ai_summary = await ai_engine.summarize_target_posture(target, findings)
        except Exception as exc:
            log.warning(f"report_tasks: AI summary unavailable, continuing without it: {exc}")

        try:
            build_result = build_report(
                target_name=target.name,
                generated_by=str(report.generated_by),
                findings=finding_dicts,
                ai_target_summary=ai_summary,
            )
            report.file_path = build_result.file_path
            report.status = ReportStatus.READY
            report.summary = ai_summary or {}
            report.finding_ids = [str(f.id) for f in findings]
            await db.commit()

            await notification_service.push_report_ready(
                user_id=str(report.generated_by), report_id=str(report.id), file_path=build_result.file_path
            )
            return {"status": "ready", "file_path": build_result.file_path}

        except ReportGenerationError as exc:
            log.error(f"report_tasks: generation failed for report {report_id}: {exc}")
            report.status = ReportStatus.FAILED
            await db.commit()
            return {"status": "failed", "error": str(exc)}
