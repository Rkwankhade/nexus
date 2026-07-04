import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.scan import Scan, ScanStatus
from models.target import Target, TargetStatus
from models.user import User
from schemas.scan import ScanCreate, ScanOut

router = APIRouter()


@router.post("/", response_model=ScanOut, status_code=201)
async def create_scan(
    payload: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    target_result = await db.execute(select(Target).where(Target.id == payload.target_id))
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if target.status not in (TargetStatus.AUTHORIZED, TargetStatus.ACTIVE):
        raise HTTPException(
            status_code=403,
            detail="Target is not authorized for scanning. Set an authorization_reference "
            "and mark the target AUTHORIZED first.",
        )

    scan = Scan(
        target_id=payload.target_id,
        initiated_by=current_user.id,
        scan_type=payload.scan_type,
        tool=payload.tool,
        parameters=payload.parameters,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Dispatch to Celery — actual tool execution lives in workers/scan_tasks.py
    from workers.scan_tasks import run_scan_task

    task = run_scan_task.delay(str(scan.id))
    scan.celery_task_id = task.id
    await db.commit()
    await db.refresh(scan)
    return scan


@router.get("/", response_model=list[ScanOut])
async def list_scans(
    target_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = select(Scan).order_by(Scan.created_at.desc())
    if target_id:
        query = query.where(Scan.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    scan = await _get_scan_or_404(db, scan_id)
    return scan


@router.post("/{scan_id}/cancel", response_model=ScanOut)
async def cancel_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    scan = await _get_scan_or_404(db, scan_id)
    if scan.status not in (ScanStatus.QUEUED, ScanStatus.RUNNING):
        raise HTTPException(status_code=400, detail="Scan is not in a cancellable state")

    if scan.celery_task_id:
        from workers.celery_app import celery_app

        celery_app.control.revoke(scan.celery_task_id, terminate=True)

    scan.status = ScanStatus.CANCELLED
    await db.commit()
    await db.refresh(scan)
    return scan


async def _get_scan_or_404(db: AsyncSession, scan_id: uuid.UUID) -> Scan:
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
