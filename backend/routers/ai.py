"""
NEXUS — /api/ai/*
Thin HTTP layer over services/ai_engine.py (Phase 4). Applies a
per-user rate limit on top of AI calls since they hit a paid API.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.dependencies import get_current_active_user
from core.redis_client import redis_client
from models.finding import Finding
from models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    context: dict = {}


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


async def _enforce_rate_limit(user: User) -> None:
    key = f"ai_rate:{user.id}"
    count = await redis_client.client.incr(key)
    if count == 1:
        await redis_client.client.expire(key, 60)
    if count > settings.AI_RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="AI request rate limit exceeded")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
):
    await _enforce_rate_limit(current_user)

    from services.ai_engine import ai_engine

    conversation_id = payload.conversation_id or str(uuid.uuid4())
    reply = await ai_engine.chat(
        user_id=str(current_user.id),
        conversation_id=conversation_id,
        message=payload.message,
        context=payload.context,
    )
    return ChatResponse(reply=reply, conversation_id=conversation_id)


@router.post("/analyze-finding/{finding_id}")
async def analyze_finding(
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _enforce_rate_limit(current_user)

    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    from services.ai_engine import ai_engine

    analysis = await ai_engine.analyze_finding(finding)
    finding.ai_analysis = analysis
    await db.commit()
    return analysis


@router.post("/suggest-exploit/{finding_id}")
async def suggest_exploit(
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _enforce_rate_limit(current_user)

    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    from services.ai_engine import ai_engine

    return await ai_engine.suggest_exploit_module(finding)


@router.post("/summarize-target/{target_id}")
async def summarize_target(
    target_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _enforce_rate_limit(current_user)

    from models.target import Target

    result = await db.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    findings_result = await db.execute(select(Finding).where(Finding.target_id == target_id))
    findings = findings_result.scalars().all()

    from services.ai_engine import ai_engine

    return await ai_engine.summarize_target_posture(target, findings)
