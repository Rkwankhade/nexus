"""
Dalfox wrapper — reflected/DOM XSS *detection* against a single authorized URL.

Scoped deliberately:
  - single-URL `url` scan mode only (no `dalfox file`/mass-scan against a
    list the caller controls, which is how this class of tool gets pointed
    at hosts outside the authorized target)
  - no blind XSS / out-of-band callback flags (`--blind`, custom `-b` URL),
    since those exfiltrate to an attacker-controlled listener rather than
    just confirming a reflection on the target itself
  - no raw flag pass-through
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url


async def run_dalfox(
    target_url: str,
    timeout_seconds: int = 300,
) -> tuple[ToolRunResult, list[dict] | None]:
    binary = require_binary("dalfox")
    safe_url = assert_safe_url(target_url)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "dalfox.json"

        argv = [
            binary,
            "url", safe_url,
            "--format", "json",
            "--silence",
            "--no-spinner",
            "-o", str(out_path),
        ]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        parsed: list[dict] | None = None
        if out_path.exists():
            try:
                raw = json.loads(out_path.read_text(errors="replace"))
                findings = raw if isinstance(raw, list) else raw.get("results", [])
                parsed = [
                    {
                        "type": f.get("type"),
                        "param": f.get("param"),
                        "payload": f.get("payload") or f.get("evidence"),
                        "severity": f.get("severity", "medium"),
                        "url": f.get("data") or f.get("url"),
                    }
                    for f in findings
                ]
            except Exception:
                parsed = None

        return result, parsed
