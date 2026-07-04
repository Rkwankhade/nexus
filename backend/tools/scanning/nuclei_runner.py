"""
Nuclei wrapper — template-based vulnerability *detection* scanning.

Only exposes safe, non-intrusive template tags (cve, exposure, misconfig,
default-logins, tech) and always runs with rate limiting. Excludes
template categories that perform active exploitation (e.g. `-tags rce`
combined with intrusive payloads) by restricting to the curated tag list
below rather than accepting arbitrary `-t`/`-tags` pass-through.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url, parse_json_lines

# Detection-oriented template categories only. Deliberately excludes
# intrusive/exploit template tags.
_SAFE_TAGS = "cve,exposure,misconfig,default-login,tech,ssl,dns"


@dataclass
class NucleiFinding:
    template_id: str
    name: str
    severity: str
    matched_at: str
    description: str = ""
    reference: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


async def run_nuclei_scan(
    target_url: str,
    severity_filter: str = "info,low,medium,high,critical",
    rate_limit: int = 50,
    timeout_seconds: int = 900,
) -> tuple[ToolRunResult, list[NucleiFinding]]:
    """Run nuclei against `target_url` using the curated detection tag set."""
    binary = require_binary("nuclei")
    safe_url = assert_safe_url(target_url)

    argv = [
        binary,
        "-u", safe_url,
        "-tags", _SAFE_TAGS,
        "-severity", severity_filter,
        "-rate-limit", str(min(rate_limit, 150)),
        "-jsonl",
        "-silent",
        "-no-interactsh",
    ]

    result = await run_command(argv, timeout_seconds=timeout_seconds)

    findings = [
        NucleiFinding(
            template_id=obj.get("template-id", obj.get("templateID", "")),
            name=obj.get("info", {}).get("name", ""),
            severity=obj.get("info", {}).get("severity", "info"),
            matched_at=obj.get("matched-at", obj.get("host", "")),
            description=obj.get("info", {}).get("description", "") or "",
            reference=obj.get("info", {}).get("reference", []) or [],
            tags=obj.get("info", {}).get("tags", []) or [],
        )
        for obj in parse_json_lines(result.stdout)
    ]

    return result, findings
