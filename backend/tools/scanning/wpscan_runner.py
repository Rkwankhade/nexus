"""
WPScan wrapper — WordPress core/plugin/theme vulnerability *detection* and
enumeration. Deliberately excludes WPScan's password-attack mode
(`--passwords`/`--usernames` brute force); only enumeration and
vulnerability-database lookup flags are exposed.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url


@dataclass
class WpScanFinding:
    component: str  # "core", "plugin:akismet", "theme:twentytwenty", etc
    title: str
    fixed_in: str = ""
    references: list[str] = field(default_factory=list)


async def run_wpscan(
    target_url: str,
    api_token: str = "",
    timeout_seconds: int = 600,
) -> tuple[ToolRunResult, list[WpScanFinding]]:
    """
    Enumerate WordPress core/plugins/themes/users on `target_url` and
    cross-reference the WPVulnDB via WPScan's vulnerability API
    (requires a free WPScan API token for vuln data; enumeration works
    without one).
    """
    binary = require_binary("wpscan")
    safe_url = assert_safe_url(target_url)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "wpscan.json"
        argv = [
            binary,
            "--url", safe_url,
            "--enumerate", "vp,vt,u",  # vulnerable plugins, vulnerable themes, users
            "--format", "json",
            "--output", str(out_path),
            "--random-user-agent",
            "--no-banner",
        ]
        if api_token:
            argv += ["--api-token", api_token]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        findings: list[WpScanFinding] = []
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text(errors="replace"))
                findings.extend(_extract_findings(data))
            except json.JSONDecodeError:
                pass

        return result, findings


def _extract_findings(data: dict) -> list[WpScanFinding]:
    findings: list[WpScanFinding] = []

    version_info = data.get("version") or {}
    for vuln in version_info.get("vulnerabilities", []):
        findings.append(
            WpScanFinding(
                component="core",
                title=vuln.get("title", ""),
                fixed_in=vuln.get("fixed_in", "") or "",
                references=_flatten_refs(vuln.get("references", {})),
            )
        )

    for plugin_name, plugin_data in (data.get("plugins") or {}).items():
        for vuln in plugin_data.get("vulnerabilities", []):
            findings.append(
                WpScanFinding(
                    component=f"plugin:{plugin_name}",
                    title=vuln.get("title", ""),
                    fixed_in=vuln.get("fixed_in", "") or "",
                    references=_flatten_refs(vuln.get("references", {})),
                )
            )

    for theme_name, theme_data in (data.get("themes") or {}).items():
        for vuln in theme_data.get("vulnerabilities", []):
            findings.append(
                WpScanFinding(
                    component=f"theme:{theme_name}",
                    title=vuln.get("title", ""),
                    fixed_in=vuln.get("fixed_in", "") or "",
                    references=_flatten_refs(vuln.get("references", {})),
                )
            )

    return findings


def _flatten_refs(references: dict) -> list[str]:
    flat: list[str] = []
    for ref_list in references.values():
        if isinstance(ref_list, list):
            flat.extend(str(r) for r in ref_list)
    return flat
