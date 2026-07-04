import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.log_entry import LogEntry, LogSource
from models.tool_job import ToolCategory, ToolJob, ToolJobStatus
from models.user import User
from schemas.tool_job import ToolJobOut

router = APIRouter()


class LogIngestRequest(BaseModel):
    source: LogSource
    host: str = ""
    event_type: str = ""
    severity: str = "info"
    message: str = ""
    raw: dict = {}


class YaraScanRequest(BaseModel):
    target_path: str
    rule_set: str = "default"


@router.post("/siem/ingest", status_code=201)
async def ingest_log(
    payload: LogIngestRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    entry = LogEntry(**payload.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    from services.log_ingestor import log_ingestor

    matches = await log_ingestor.evaluate_rules(entry)
    if matches:
        entry.matched_rules = matches
        await db.commit()
    return {"id": str(entry.id), "matched_rules": matches}


@router.get("/siem/logs")
async def list_logs(
    source: LogSource | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = select(LogEntry).order_by(LogEntry.ingested_at.desc()).limit(min(limit, 500))
    if source:
        query = query.where(LogEntry.source == source)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/yara/scan", response_model=ToolJobOut, status_code=201)
async def yara_scan(
    payload: YaraScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    job = ToolJob(
        requested_by=current_user.id,
        category=ToolCategory.BLUETEAM,
        tool_name="yara_scanner",
        command="",
        status=ToolJobStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from workers.scan_tasks import run_tool_job_task

    task = run_tool_job_task.delay(str(job.id), payload.model_dump())
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/rules")
async def list_detection_rules(_: User = Depends(get_current_active_user)):
    from services.log_ingestor import log_ingestor

    return await log_ingestor.list_rules()
