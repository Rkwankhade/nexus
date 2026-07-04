import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.target import Target, TargetStatus
from models.user import User
from schemas.target import TargetCreate, TargetOut, TargetUpdate

router = APIRouter()


@router.post("/", response_model=TargetOut, status_code=201)
async def create_target(
    payload: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst_or_admin),
):
    target = Target(**payload.model_dump(), owner_id=current_user.id)
    # A target without a documented authorization reference stays
    # PENDING_AUTH regardless of who creates it — it cannot be scanned
    # or exploited until an admin marks it AUTHORIZED with a reference.
    if payload.authorization_reference:
        target.status = TargetStatus.AUTHORIZED
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/", response_model=list[TargetOut])
async def list_targets(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Target).order_by(Target.created_at.desc()))
    return result.scalars().all()


@router.get("/{target_id}", response_model=TargetOut)
async def get_target(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    target = await _get_target_or_404(db, target_id)
    return target


@router.patch("/{target_id}", response_model=TargetOut)
async def update_target(
    target_id: uuid.UUID,
    payload: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    target = await _get_target_or_404(db, target_id)
    updates = payload.model_dump(exclude_unset=True)

    # Guard: only allow AUTHORIZED/ACTIVE status if an authorization
    # reference exists (either already on file, or provided now).
    new_status = updates.get("status")
    ref = updates.get("authorization_reference", target.authorization_reference)
    if new_status in (TargetStatus.AUTHORIZED, TargetStatus.ACTIVE) and not ref:
        raise HTTPException(
            status_code=400,
            detail="Cannot authorize a target without an authorization_reference",
        )

    for field, value in updates.items():
        setattr(target, field, value)

    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    target = await _get_target_or_404(db, target_id)
    await db.delete(target)
    await db.commit()


async def _get_target_or_404(db: AsyncSession, target_id: uuid.UUID) -> Target:
    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target
