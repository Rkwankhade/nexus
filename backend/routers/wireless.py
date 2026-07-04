import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import require_analyst_or_admin
from models.target import Target, TargetStatus, TargetType
from models.tool_job import ToolCategory, ToolJob, ToolJobStatus
from models.user import User
from schemas.tool_job import ToolJobOut

router = APIRouter()


class WirelessScanRequest(BaseModel):
    interface: str = "wlan0mon"
    channel: int | None = None
    duration_seconds: int = 60


class WirelessAssessRequest(BaseModel):
    target_id: uuid.UUID
    interface: str = "wlan0mon"


@router.post("/scan", response_model=ToolJobOut, status_code=201)
async def wireless_scan(
    payload: WirelessScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    Passive discovery of nearby SSIDs/BSSIDs — does not target or
    attack a specific authorized network, so no Target authorization
    check is required here (equivalent to airodump-ng in scan mode).
    """
    job = ToolJob(
        requested_by=current_user.id,
        category=ToolCategory.WIRELESS,
        tool_name="aircrack_runner",
        status=ToolJobStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from workers.scan_tasks import run_tool_job_task

    task = run_tool_job_task.delay(str(job.id), {"mode": "scan", **payload.model_dump()})
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)
    return job


@router.post("/assess", response_model=ToolJobOut, status_code=201)
async def wireless_assess(
    payload: WirelessAssessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    Active assessment (handshake capture + offline key strength test)
    against a specific SSID — requires the SSID to be a registered,
    AUTHORIZED Target, same as any other active engagement action.
    """
    result = await db.execute(select(Target).where(Target.id == payload.target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if target.type != TargetType.WIRELESS_SSID:
        raise HTTPException(status_code=400, detail="Target is not a wireless_ssid type")
    if target.status not in (TargetStatus.AUTHORIZED, TargetStatus.ACTIVE):
        raise HTTPException(
            status_code=403, detail="Target is not authorized for wireless assessment"
        )

    job = ToolJob(
        target_id=target.id,
        requested_by=current_user.id,
        category=ToolCategory.WIRELESS,
        tool_name="wifite_runner",
        status=ToolJobStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    from workers.scan_tasks import run_tool_job_task

    task = run_tool_job_task.delay(
        str(job.id), {"mode": "assess", "ssid": target.value, **payload.model_dump()}
    )
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)
    return job
