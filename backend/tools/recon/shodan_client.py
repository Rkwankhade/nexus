"""
Shodan API client — read-only lookups against Shodan's indexed internet
scan data. This never scans the target itself; it queries Shodan's
existing dataset, which is why it's implemented as an HTTP client rather
than a subprocess tool wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import httpx

from core.config import settings
from utils.logger import get_logger
from utils.parser_utils import assert_safe_hostname_or_ip

log = get_logger(__name__)

_BASE_URL = "https://api.shodan.io"


class ShodanNotConfiguredError(RuntimeError):
    pass


class ShodanAPIError(RuntimeError):
    pass


@dataclass
class ShodanHostResult:
    ip_str: str
    org: str = ""
    os: Optional[str] = None
    ports: list[int] = field(default_factory=list)
    hostnames: list[str] = field(default_factory=list)
    vulns: list[str] = field(default_factory=list)
    banners: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def _require_api_key() -> str:
    if not settings.SHODAN_API_KEY:
        raise ShodanNotConfiguredError(
            "SHODAN_API_KEY is not set. Add it to .env to enable Shodan lookups."
        )
    return settings.SHODAN_API_KEY


async def lookup_host(ip_address: str, timeout_seconds: int = 30) -> ShodanHostResult:
    """Look up a single IP's Shodan host record (passive — no active scanning)."""
    api_key = _require_api_key()
    safe_ip = assert_safe_hostname_or_ip(ip_address)

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.get(
            f"{_BASE_URL}/shodan/host/{safe_ip}",
            params={"key": api_key},
        )

    if response.status_code == 404:
        return ShodanHostResult(ip_str=safe_ip)
    if response.status_code != 200:
        raise ShodanAPIError(
            f"Shodan API returned {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    banners = [
        {
            "port": item.get("port"),
            "transport": item.get("transport", "tcp"),
            "product": item.get("product", ""),
            "data": (item.get("data") or "")[:2000],
        }
        for item in data.get("data", [])
    ]

    return ShodanHostResult(
        ip_str=data.get("ip_str", safe_ip),
        org=data.get("org", "") or "",
        os=data.get("os"),
        ports=data.get("ports", []) or [],
        hostnames=data.get("hostnames", []) or [],
        vulns=list(data.get("vulns", []) or []),
        banners=banners,
        raw=data,
    )


async def search_shodan(query: str, limit: int = 20, timeout_seconds: int = 30) -> list[dict]:
    """
    Run a Shodan search query (e.g. 'org:"Example Corp" port:443') and
    return up to `limit` matches. Intended for asset-discovery use during
    authorized recon of an org's own known infrastructure.
    """
    api_key = _require_api_key()

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.get(
            f"{_BASE_URL}/shodan/host/search",
            params={"key": api_key, "query": query, "limit": min(limit, 100)},
        )

    if response.status_code != 200:
        raise ShodanAPIError(
            f"Shodan API returned {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    return data.get("matches", [])[:limit]
