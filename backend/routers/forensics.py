import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.tool_job import ToolCategory, ToolJob, ToolJobStatus
from models.user import User
from schemas.tool_job import ToolJobOut

router = APIRouter()


class MemoryAnalysisRequest(BaseModel):
    image_path: str
    profile: str = "auto"
    plugins: list[str] = ["pslist", "netscan", "malfind"]


class PcapAnalysisRequest(BaseModel):
    pcap_path: str


class MalwareScanRequest(BaseModel):
    file_path: str
    deep_scan: bool = False


class DiskAnalysisRequest(BaseModel):
    image_path: str
    filesystem: str = "auto"
    modules: list[str] = ["timeline", "deleted_files", "registry", "browser_artifacts"]


async def _dispatch_forensics_job(
    db: AsyncSession, user: User, tool_name: str, parameters: dict
) -> ToolJob:
    job = ToolJob(
        requested_by=user.id,
        category=ToolCategory.FORENSICS,
        tool_name=tool_name,
        status=ToolJobStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from workers.scan_tasks import run_tool_job_task

    task = run_tool_job_task.delay(str(job.id), parameters)
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/memory/analyze", response_model=ToolJobOut, status_code=201)
async def analyze_memory(
    payload: MemoryAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return await _dispatch_forensics_job(
        db, current_user, "volatility_runner", payload.model_dump()
    )


@router.post("/pcap/analyze", response_model=ToolJobOut, status_code=201)
async def analyze_pcap(
    payload: PcapAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return await _dispatch_forensics_job(
        db, current_user, "pcap_analyzer", payload.model_dump()
    )


@router.post("/malware/scan", response_model=ToolJobOut, status_code=201)
async def scan_malware(
    payload: MalwareScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return await _dispatch_forensics_job(
        db, current_user, "yara_malware_scanner", payload.model_dump()
    )


@router.post("/disk/analyze", response_model=ToolJobOut, status_code=201)
async def analyze_disk(
    payload: DiskAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    return await _dispatch_forensics_job(
        db, current_user, "autopsy_runner", payload.model_dump()
    )


@router.get("/jobs/{job_id}", response_model=ToolJobOut)
async def get_forensics_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    result = await db.execute(select(ToolJob).where(ToolJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
