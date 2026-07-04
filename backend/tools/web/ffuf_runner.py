"""
ffuf wrapper — content/directory discovery only.

Exposes wordlist-based path and vhost discovery (finding what's reachable on
a web server) with an allowlisted flag set. Does not expose ffuf's raw
argument pass-through, POST-data fuzzing against auth/login endpoints, or
any injection-payload wordlist mode — this stays a discovery tool, not a
generic fuzzing/exploitation harness.
"""

from __future__ import annotations

import enum
import json
import tempfile
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url

# A small set of vetted, non-destructive wordlists shipped with the platform.
# Operators can extend this list in config, but arbitrary local file paths
# from the request body are never accepted directly.
_ALLOWED_WORDLISTS = {
    "common": "/usr/share/nexus/wordlists/common-paths.txt",
    "small": "/usr/share/nexus/wordlists/small-paths.txt",
    "api": "/usr/share/nexus/wordlists/api-endpoints.txt",
}


class FfufMode(str, enum.Enum):
    PATH_DISCOVERY = "path_discovery"   # FUZZ in the URL path
    VHOST_DISCOVERY = "vhost_discovery"  # FUZZ in the Host header


async def run_ffuf(
    base_url: str,
    mode: FfufMode = FfufMode.PATH_DISCOVERY,
    wordlist: str = "common",
    match_codes: str = "200,204,301,302,307,401,403",
    threads: int = 20,
    timeout_seconds: int = 300,
) -> tuple[ToolRunResult, list[dict] | None]:
    binary = require_binary("ffuf")
    safe_url = assert_safe_url(base_url)

    if wordlist not in _ALLOWED_WORDLISTS:
        raise ValueError(f"Unknown wordlist profile: {wordlist!r}")
    wordlist_path = _ALLOWED_WORDLISTS[wordlist]

    threads = max(1, min(threads, 40))  # cap concurrency

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "ffuf.json"

        if mode == FfufMode.PATH_DISCOVERY:
            target = safe_url.rstrip("/") + "/FUZZ"
            argv = [
                binary,
                "-u", target,
                "-w", wordlist_path,
                "-mc", match_codes,
                "-t", str(threads),
                "-of", "json",
                "-o", str(out_path),
                "-silent",
            ]
        else:  # VHOST_DISCOVERY
            argv = [
                binary,
                "-u", safe_url,
                "-H", "Host: FUZZ",
                "-w", wordlist_path,
                "-mc", match_codes,
                "-t", str(threads),
                "-of", "json",
                "-o", str(out_path),
                "-silent",
            ]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        parsed: list[dict] | None = None
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text(errors="replace"))
                parsed = [
                    {
                        "input": r.get("input", {}).get("FUZZ"),
                        "url": r.get("url"),
                        "status": r.get("status"),
                        "length": r.get("length"),
                        "words": r.get("words"),
                    }
                    for r in data.get("results", [])
                ]
            except Exception:
                parsed = None

        return result, parsed
