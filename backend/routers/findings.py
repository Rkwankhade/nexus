import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.finding import Finding, Severity
from models.user import User
from schemas.finding import FindingCreate, FindingOut, FindingUpdate

router = APIRouter()


@router.post("/", response_model=FindingOut, status_code=201)
async def create_finding(
    payload: FindingCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    finding = Finding(**payload.model_dump())
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.get("/", response_model=list[FindingOut])
async def list_findings(
    target_id: uuid.UUID | None = None,
    severity: Severity | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = select(Finding).order_by(Finding.created_at.desc())
    if target_id:
        query = query.where(Finding.target_id == target_id)
    if severity:
        query = query.where(Finding.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{finding_id}", response_model=FindingOut)
async def get_finding(
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await _get_finding_or_404(db, finding_id)


@router.patch("/{finding_id}", response_model=FindingOut)
async def update_finding(
    finding_id: uuid.UUID,
    payload: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    finding = await _get_finding_or_404(db, finding_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(finding, field, value)
    await db.commit()
    await db.refresh(finding)
    return finding


@router.delete("/{finding_id}", status_code=204)
async def delete_finding(
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    finding = await _get_finding_or_404(db, finding_id)
    await db.delete(finding)
    await db.commit()


async def _get_finding_or_404(db: AsyncSession, finding_id: uuid.UUID) -> Finding:
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding
