import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.report import Report, ReportStatus
from models.user import User
from schemas.report import ReportCreate, ReportOut

router = APIRouter()


@router.post("/", response_model=ReportOut, status_code=201)
async def create_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    report = Report(
        target_id=payload.target_id,
        generated_by=current_user.id,
        title=payload.title,
        format=payload.format,
        finding_ids=[str(f) for f in payload.finding_ids],
        status=ReportStatus.GENERATING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    from workers.report_tasks import generate_report_task

    generate_report_task.delay(str(report.id))
    return report


@router.get("/", response_model=list[ReportOut])
async def list_reports(
    target_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = select(Report).order_by(Report.created_at.desc())
    if target_id:
        query = query.where(Report.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await _get_report_or_404(db, report_id)


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    report = await _get_report_or_404(db, report_id)
    if report.status != ReportStatus.READY or not report.file_path:
        raise HTTPException(status_code=400, detail="Report is not ready yet")
    return FileResponse(
        report.file_path,
        media_type="application/octet-stream",
        filename=f"{report.title}.{report.format.value}",
    )


async def _get_report_or_404(db: AsyncSession, report_id: uuid.UUID) -> Report:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
