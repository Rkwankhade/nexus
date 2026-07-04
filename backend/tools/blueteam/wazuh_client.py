"""
Wazuh client — REST API client for the Wazuh manager (agent inventory,
alerts, vulnerability summaries). Read/management operations against
NEXUS's own defensive SIEM/EDR deployment — no offensive capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import httpx

from utils.logger import get_logger

log = get_logger(__name__)


class WazuhAuthError(RuntimeError):
    pass


class WazuhAPIError(RuntimeError):
    pass


@dataclass
class WazuhAgent:
    id: str
    name: str
    ip: str
    status: str
    os_platform: str = ""
    version: str = ""
    last_keep_alive: str = ""


@dataclass
class WazuhAlert:
    timestamp: str
    rule_id: str
    rule_description: str
    rule_level: int
    agent_name: str
    agent_id: str
    full_log: str = ""
    raw: dict = field(default_factory=dict)


class WazuhClient:
    """
    Async client for the Wazuh manager REST API.

    Usage:
        async with WazuhClient(base_url, username, password) as client:
            agents = await client.list_agents()
    """

    def __init__(self, base_url: str, username: str, password: str, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self._token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "WazuhClient":
        self._client = httpx.AsyncClient(verify=self.verify_tls, timeout=30)
        await self._authenticate()
        return self

    async def __aexit__(self, *exc_info):
        if self._client:
            await self._client.aclose()

    async def _authenticate(self) -> None:
        assert self._client is not None
        response = await self._client.post(
            f"{self.base_url}/security/user/authenticate",
            auth=(self.username, self.password),
        )
        if response.status_code != 200:
            raise WazuhAuthError(f"Wazuh authentication failed: {response.status_code} {response.text[:200]}")
        self._token = response.json()["data"]["token"]

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        assert self._client is not None
        response = await self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params or {})
        if response.status_code == 401:
            await self._authenticate()
            response = await self._client.get(f"{self.base_url}{path}", headers=self._headers(), params=params or {})
        if response.status_code != 200:
            raise WazuhAPIError(f"Wazuh API {path} returned {response.status_code}: {response.text[:300]}")
        return response.json()

    async def list_agents(self, status: Optional[str] = None, limit: int = 100) -> list[WazuhAgent]:
        params = {"limit": limit}
        if status:
            params["status"] = status
        data = await self._get("/agents", params=params)

        agents = []
        for item in data.get("data", {}).get("affected_items", []):
            os_info = item.get("os", {}) or {}
            agents.append(
                WazuhAgent(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    ip=item.get("ip", ""),
                    status=item.get("status", "unknown"),
                    os_platform=os_info.get("platform", ""),
                    version=item.get("version", ""),
                    last_keep_alive=item.get("lastKeepAlive", ""),
                )
            )
        return agents

    async def get_recent_alerts(self, limit: int = 100, min_level: int = 0) -> list[WazuhAlert]:
        """
        Fetch recent alerts from the manager's alert summary endpoint.
        For high-volume production use, prefer querying the Wazuh Indexer
        (OpenSearch) directly rather than this manager-API convenience call.
        """
        data = await self._get("/manager/logs/summary")
        alerts: list[WazuhAlert] = []
        for entry in data.get("data", {}).get("affected_items", [])[:limit]:
            level = entry.get("level", 0)
            if level < min_level:
                continue
            alerts.append(
                WazuhAlert(
                    timestamp=entry.get("timestamp", ""),
                    rule_id=str(entry.get("rule_id", "")),
                    rule_description=entry.get("description", ""),
                    rule_level=level,
                    agent_name=entry.get("agent_name", ""),
                    agent_id=entry.get("agent_id", ""),
                    full_log=entry.get("full_log", ""),
                    raw=entry,
                )
            )
        return alerts

    async def get_agent_vulnerabilities(self, agent_id: str, limit: int = 100) -> list[dict]:
        """Fetch the Wazuh vulnerability-detector summary for a single agent."""
        data = await self._get(f"/vulnerability/{agent_id}", params={"limit": limit})
        return data.get("data", {}).get("affected_items", [])

    async def restart_agent(self, agent_id: str) -> bool:
        """Request a config/service restart on an agent (agent-side operation, not an attack)."""
        assert self._client is not None
        response = await self._client.put(
            f"{self.base_url}/agents/{agent_id}/restart",
            headers=self._headers(),
        )
        return response.status_code == 200
