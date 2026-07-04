"""
Nikto wrapper — web server misconfiguration/known-issue detection scan.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url


@dataclass
class NiktoFinding:
    id: str
    method: str
    url: str
    message: str


async def run_nikto_scan(
    target_url: str,
    timeout_seconds: int = 900,
) -> tuple[ToolRunResult, list[NiktoFinding]]:
    """Run nikto against `target_url` and parse its JSON report output."""
    binary = require_binary("nikto")
    safe_url = assert_safe_url(target_url)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "nikto.json"
        argv = [
            binary,
            "-h", safe_url,
            "-Format", "json",
            "-output", str(out_path),
            "-ask", "no",
        ]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        findings: list[NiktoFinding] = []
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text(errors="replace"))
                vulnerabilities = data.get("vulnerabilities", [])
                for item in vulnerabilities:
                    findings.append(
                        NiktoFinding(
                            id=item.get("id", ""),
                            method=item.get("method", "GET"),
                            url=item.get("url", safe_url),
                            message=item.get("msg", ""),
                        )
                    )
            except json.JSONDecodeError:
                pass

        return result, findings
