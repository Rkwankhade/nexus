import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_active_user, require_analyst_or_admin
from models.alert import Alert, AlertSeverity, AlertStatus
from models.user import User
from schemas.alert import AlertOut, AlertUpdate

router = APIRouter()


@router.get("/", response_model=list[AlertOut])
async def list_alerts(
    status_filter: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    query = select(Alert).order_by(Alert.created_at.desc())
    if status_filter:
        query = query.where(Alert.status == status_filter)
    if severity:
        query = query.where(Alert.severity == severity)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return await _get_alert_or_404(db, alert_id)


@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst_or_admin),
):
    alert = await _get_alert_or_404(db, alert_id)
    alert.status = payload.status
    await db.commit()
    await db.refresh(alert)
    return alert


async def _get_alert_or_404(db: AsyncSession, alert_id: uuid.UUID) -> Alert:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
