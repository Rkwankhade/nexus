"""
Tool orchestrator — central dispatch layer between the API/worker layer
and the individual tool wrapper modules under tools/.

Scope note: this orchestrator only dispatches to the tool categories
NEXUS actually implements: recon, scanning (detection-only), blueteam,
and forensics. It has no dispatch table entries for exploitation,
password-cracking, post-exploitation, wireless-attack, or web-attack
tooling — those tool wrapper modules don't exist in this build, so
requests naming those categories fail closed with a clear error rather
than silently doing nothing or falling through to a shell call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from models.finding import Finding, Severity
from models.scan import ScanType
from tools.recon import amass_runner, dnsx_runner, nmap_runner, theharvester_runner, whois_runner
from tools.scanning import nikto_runner, nuclei_runner, wpscan_runner
from utils.logger import get_logger

log = get_logger(__name__)

ProgressCallback = Optional[Callable[[int, str], None]]


class UnsupportedToolError(ValueError):
    """Raised for any tool/category NEXUS does not implement dispatch for.
    In particular: exploitation, password, post_exploit, wireless, and web
    (sqlmap/ffuf/dalfox-class) categories are intentionally absent."""


@dataclass
class ScanDispatchResult:
    succeeded: bool
    raw_output: dict[str, Any] = field(default_factory=dict)
    findings_created: int = 0


# Registry of dispatchable tools. Only recon/scanning wrappers that are
# actually implemented in this build are registered here.
_RECON_TOOLS = {"nmap", "amass", "theharvester", "whois", "dnsx"}
_SCANNING_TOOLS = {"nuclei", "nikto", "wpscan"}
_SUPPORTED_TOOLS = _RECON_TOOLS | _SCANNING_TOOLS


async def run_scan_tool(
    tool_name: str,
    scan_type: ScanType,
    parameters: dict[str, Any],
    on_progress: ProgressCallback = None,
) -> dict[str, Any]:
    """
    Dispatch a scan job to the appropriate tool wrapper based on
    `tool_name`. Returns a plain dict (not the dataclass) since this is
    consumed directly by workers/scan_tasks.py and persisted to JSONB.
    """
    tool_key = tool_name.lower().strip()
    if tool_key not in _SUPPORTED_TOOLS:
        raise UnsupportedToolError(
            f"'{tool_name}' is not a supported scan tool in this NEXUS build. "
            f"Supported: {sorted(_SUPPORTED_TOOLS)}"
        )

    if on_progress:
        on_progress(10, f"Launching {tool_name}")

    dispatch_map: dict[str, Callable] = {
        "nmap": _run_nmap,
        "amass": _run_amass,
        "theharvester": _run_theharvester,
        "whois": _run_whois,
        "dnsx": _run_dnsx,
        "nuclei": _run_nuclei,
        "nikto": _run_nikto,
        "wpscan": _run_wpscan,
    }

    handler = dispatch_map[tool_key]
    result = await handler(parameters)

    if on_progress:
        on_progress(90, f"{tool_name} finished, persisting results")

    return {
        "succeeded": result.succeeded,
        "raw_output": result.raw_output,
        "findings_created": result.findings_created,
    }


# ---------------------------------------------------------------------------
# Individual tool handlers — each normalizes its tool's output into the
# common ScanDispatchResult shape. None of these create Finding rows
# directly; they return structured data for the caller (scan_tasks) to
# persist within its own DB session/transaction.
# ---------------------------------------------------------------------------


async def _run_nmap(params: dict[str, Any]) -> ScanDispatchResult:
    target = params["target"]
    profile = nmap_runner.ScanProfile(params.get("profile", "service_version"))
    result, parsed = await nmap_runner.run_nmap_scan(target, profile=profile, timeout_seconds=params.get("timeout_seconds", 900))

    raw = {
        "returncode": result.returncode,
        "hosts": [
            {
                "address": h.address,
                "status": h.status,
                "ports": [{"port": p.port, "protocol": p.protocol, "state": p.state, "service": p.service} for p in h.ports],
            }
            for h in (parsed.hosts if parsed else [])
        ],
    }
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=raw)


async def _run_amass(params: dict[str, Any]) -> ScanDispatchResult:
    result, subdomains = await amass_runner.run_amass_enum(
        params["domain"], passive_only=params.get("passive_only", True), timeout_seconds=params.get("timeout_seconds", 900)
    )
    return ScanDispatchResult(succeeded=result.succeeded, raw_output={"subdomains": subdomains})


async def _run_theharvester(params: dict[str, Any]) -> ScanDispatchResult:
    result, data = await theharvester_runner.run_theharvester(
        params["domain"], sources=params.get("sources"), timeout_seconds=params.get("timeout_seconds", 600)
    )
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=data)


async def _run_whois(params: dict[str, Any]) -> ScanDispatchResult:
    result, data = await whois_runner.run_whois(params["domain"], timeout_seconds=params.get("timeout_seconds", 30))
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=data)


async def _run_dnsx(params: dict[str, Any]) -> ScanDispatchResult:
    result, records = await dnsx_runner.run_dnsx(params["hosts"], timeout_seconds=params.get("timeout_seconds", 300))
    return ScanDispatchResult(succeeded=result.succeeded, raw_output={"records": records})


async def _run_nuclei(params: dict[str, Any]) -> ScanDispatchResult:
    result, findings = await nuclei_runner.run_nuclei_scan(
        params["target_url"],
        severity_filter=params.get("severity_filter", "info,low,medium,high,critical"),
        rate_limit=params.get("rate_limit", 50),
        timeout_seconds=params.get("timeout_seconds", 900),
    )
    raw = {"findings": [f.__dict__ for f in findings]}
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=raw, findings_created=len(findings))


async def _run_nikto(params: dict[str, Any]) -> ScanDispatchResult:
    result, findings = await nikto_runner.run_nikto_scan(params["target_url"], timeout_seconds=params.get("timeout_seconds", 900))
    raw = {"findings": [f.__dict__ for f in findings]}
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=raw, findings_created=len(findings))


async def _run_wpscan(params: dict[str, Any]) -> ScanDispatchResult:
    result, findings = await wpscan_runner.run_wpscan(params["target_url"], timeout_seconds=params.get("timeout_seconds", 900))
    raw = {"findings": [f.__dict__ for f in findings]}
    return ScanDispatchResult(succeeded=result.succeeded, raw_output=raw, findings_created=len(findings))


def build_finding_from_generic(
    target_id: str,
    scan_id: str,
    title: str,
    description: str,
    severity_label: str,
    source_tool: str,
    evidence: Optional[dict] = None,
    affected_host: str = "",
    affected_port: Optional[int] = None,
) -> Finding:
    """Helper for turning a normalized tool finding dict into a Finding ORM
    instance, used by scan_tasks/routers after a scan's raw_output is
    parsed. Centralized here so severity-string normalization is
    consistent across every tool wrapper's differing severity vocab."""
    severity = _normalize_severity(severity_label)
    return Finding(
        target_id=target_id,
        scan_id=scan_id,
        title=title,
        description=description,
        severity=severity,
        source_tool=source_tool,
        evidence=evidence or {},
        affected_host=affected_host,
        affected_port=affected_port,
    )


def _normalize_severity(label: str) -> Severity:
    normalized = (label or "info").strip().lower()
    mapping = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "moderate": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
        "informational": Severity.INFO,
        "unknown": Severity.INFO,
    }
    return mapping.get(normalized, Severity.INFO)
