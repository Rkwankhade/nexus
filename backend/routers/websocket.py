"""
NEXUS — /ws/*
Real-time channels. Auth is via a `token` query param (JWT access
token) since browser WebSocket clients can't set Authorization
headers. Each connection subscribes to a Redis pub/sub channel that
services/notification_service.py publishes to whenever a ToolJob,
Scan, ExploitAttempt, or Alert changes state.
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from core.redis_client import redis_client
from core.security import decode_token

logger = logging.getLogger("nexus.websocket")
router = APIRouter()


async def _authenticate(websocket: WebSocket, token: str) -> str | None:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return None
    return payload["sub"]


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_stream(websocket: WebSocket, job_id: str, token: str = Query(...)):
    """Live stdout/progress stream for a single ToolJob or Scan."""
    await websocket.accept()
    user_id = await _authenticate(websocket, token)
    if not user_id:
        return

    channel = f"job:{job_id}"
    try:
        async for message in redis_client.subscribe(channel):
            await websocket.send_json(message)
    except WebSocketDisconnect:
        logger.info("Client disconnected from job stream %s", job_id)
    except Exception:
        logger.exception("Error streaming job %s", job_id)
        await websocket.close(code=1011)


@router.websocket("/ws/notifications")
async def notifications_stream(websocket: WebSocket, token: str = Query(...)):
    """Global notification feed: new alerts, exploit approvals needed, etc."""
    await websocket.accept()
    user_id = await _authenticate(websocket, token)
    if not user_id:
        return

    channel = f"notifications:{user_id}"
    global_channel = "notifications:broadcast"
    try:
        queue: asyncio.Queue = asyncio.Queue()

        async def pump(chan: str):
            async for message in redis_client.subscribe(chan):
                await queue.put(message)

        tasks = [
            asyncio.create_task(pump(channel)),
            asyncio.create_task(pump(global_channel)),
        ]
        try:
            while True:
                message = await queue.get()
                await websocket.send_json(message)
        finally:
            for t in tasks:
                t.cancel()
    except WebSocketDisconnect:
        logger.info("Client disconnected from notifications")
    except Exception:
        logger.exception("Error streaming notifications")
        await websocket.close(code=1011)


@router.websocket("/ws/terminal/{job_id}")
async def terminal_stream(websocket: WebSocket, job_id: str, token: str = Query(...)):
    """
    Raw line-buffered terminal output for xterm.js on the frontend —
    same underlying channel as job_progress_stream but pre-formatted
    as plain text lines instead of structured JSON.
    """
    await websocket.accept()
    user_id = await _authenticate(websocket, token)
    if not user_id:
        return

    channel = f"job:{job_id}"
    try:
        async for message in redis_client.subscribe(channel):
            line = message.get("line") or json.dumps(message)
            await websocket.send_text(line)
    except WebSocketDisconnect:
        logger.info("Client disconnected from terminal stream %s", job_id)
    except Exception:
        logger.exception("Error streaming terminal %s", job_id)
        await websocket.close(code=1011)
