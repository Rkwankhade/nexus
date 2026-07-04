"""
theHarvester wrapper — OSINT email/subdomain/host gathering from public
sources (search engines, certificate transparency, public APIs).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip

_DEFAULT_SOURCES = "crtsh,otx,hackertarget,rapiddns"


async def run_theharvester(
    domain: str,
    sources: str = _DEFAULT_SOURCES,
    timeout_seconds: int = 300,
) -> tuple[ToolRunResult, dict]:
    """
    Run theHarvester against `domain` using passive OSINT sources and
    return (raw_result, parsed_json). parsed_json contains keys like
    'emails', 'hosts', 'ips' when theHarvester successfully wrote JSON.
    """
    binary = require_binary("theHarvester")
    safe_domain = assert_safe_hostname_or_ip(domain)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "harvest"
        argv = [
            binary,
            "-d", safe_domain,
            "-b", sources,
            "-f", str(out_path),
        ]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        parsed: dict = {}
        json_path = out_path.with_suffix(".json")
        if json_path.exists():
            try:
                parsed = json.loads(json_path.read_text(errors="replace"))
            except json.JSONDecodeError:
                parsed = {}

        return result, parsed
