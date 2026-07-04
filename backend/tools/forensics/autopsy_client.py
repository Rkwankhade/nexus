"""
Autopsy client — thin async HTTP client over Autopsy's case/data-source
REST API (exposed via the Autopsy REST middleware plugin, typically on
localhost:9999 in an Autopsy server deployment). Handles case creation,
disk-image ingestion job submission, and polling for results/artifacts.

This module only orchestrates *existing* Autopsy ingest modules (hash
lookup, file-type ID, keyword search, etc.) through its documented API —
it does not implement any disk-parsing logic itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from core.config import get_settings
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AutopsyCase:
    case_id: str
    case_name: str
    created_at: str


@dataclass
class IngestJobStatus:
    job_id: str
    case_id: str
    status: str  # "pending" | "running" | "completed" | "failed"
    progress_percent: float = 0.0


@dataclass
class AutopsyArtifact:
    artifact_id: str
    artifact_type: str
    source_file: str
    attributes: dict = field(default_factory=dict)


class AutopsyClientError(RuntimeError):
    pass


class AutopsyClient:
    """Async client for a running Autopsy REST endpoint. Instantiate once per
    request/task via `get_autopsy_client()` below rather than constructing
    directly, so the base URL/timeout stay centrally configured."""

    def __init__(self, base_url: str, timeout_seconds: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as exc:
            log.error(f"Autopsy API error {exc.response.status_code} on {path}: {exc.response.text[:500]}")
            raise AutopsyClientError(f"Autopsy API returned {exc.response.status_code} for {path}") from exc
        except httpx.RequestError as exc:
            log.error(f"Autopsy API request failed for {path}: {exc}")
            raise AutopsyClientError(f"Could not reach Autopsy server at {self._base_url}: {exc}") from exc

    async def create_case(self, case_name: str, base_directory: str) -> AutopsyCase:
        payload = {"caseName": case_name, "baseDirectory": base_directory}
        data = await self._request("POST", "/api/case", json=payload)
        return AutopsyCase(
            case_id=data["caseId"],
            case_name=data.get("caseName", case_name),
            created_at=data.get("createdAt", ""),
        )

    async def add_data_source(self, case_id: str, image_path: str, timezone: str = "UTC") -> str:
        """Register a disk image (E01/DD/raw) as a data source in an existing
        case. Returns the data-source ID Autopsy assigns."""
        payload = {"caseId": case_id, "imagePath": image_path, "timeZone": timezone}
        data = await self._request("POST", "/api/data-source", json=payload)
        return data["dataSourceId"]

    async def start_ingest(
        self,
        case_id: str,
        data_source_id: str,
        modules: Optional[list[str]] = None,
    ) -> IngestJobStatus:
        """
        Kick off an ingest job using the requested Autopsy ingest modules
        (e.g. ["Hash Lookup", "File Type Identification", "Keyword Search",
        "Recent Activity", "Photo Rec Carver"]). Defaults to Autopsy's
        standard module set if none specified.
        """
        payload = {
            "caseId": case_id,
            "dataSourceId": data_source_id,
            "modules": modules or ["Hash Lookup", "File Type Identification", "Recent Activity", "Keyword Search"],
        }
        data = await self._request("POST", "/api/ingest/start", json=payload)
        return IngestJobStatus(
            job_id=data["jobId"],
            case_id=case_id,
            status=data.get("status", "pending"),
            progress_percent=float(data.get("progressPercent", 0.0)),
        )

    async def get_ingest_status(self, job_id: str) -> IngestJobStatus:
        data = await self._request("GET", f"/api/ingest/{job_id}")
        return IngestJobStatus(
            job_id=job_id,
            case_id=data.get("caseId", ""),
            status=data.get("status", "unknown"),
            progress_percent=float(data.get("progressPercent", 0.0)),
        )

    async def list_artifacts(
        self,
        case_id: str,
        artifact_type: Optional[str] = None,
        limit: int = 500,
    ) -> list[AutopsyArtifact]:
        """
        Fetch blackboard artifacts (Autopsy's term for extracted findings —
        web history, installed programs, EXIF metadata, keyword hits, etc.)
        for a case, optionally filtered by artifact type.
        """
        params: dict[str, Any] = {"limit": limit}
        if artifact_type:
            params["type"] = artifact_type
        data = await self._request("GET", f"/api/case/{case_id}/artifacts", params=params)
        return [
            AutopsyArtifact(
                artifact_id=item["artifactId"],
                artifact_type=item["artifactType"],
                source_file=item.get("sourceFile", ""),
                attributes=item.get("attributes", {}),
            )
            for item in data.get("artifacts", [])
        ]

    async def close_case(self, case_id: str) -> None:
        await self._request("POST", f"/api/case/{case_id}/close")


def get_autopsy_client() -> AutopsyClient:
    """Factory reading the Autopsy REST endpoint from centralized settings
    (backend/core/config.py), consistent with how other tool clients such
    as shodan_client.py resolve their endpoints/credentials."""
    settings = get_settings()
    base_url = getattr(settings, "AUTOPSY_API_URL", "http://localhost:9999")
    return AutopsyClient(base_url=base_url)
