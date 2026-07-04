"""
wfuzz wrapper — GET parameter/path fuzzing for content discovery only.

Same scoping philosophy as ffuf_runner: allowlisted wordlists, fixed hide/show
filters, no raw flag pass-through, and no payload categories built for
injection testing (SQLi/XSS payload lists are intentionally excluded — use
the dedicated scanning-layer tools like Nuclei/Nikto/Dalfox for detection).
"""

from __future__ import annotations

import re

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_url

_ALLOWED_WORDLISTS = {
    "common": "/usr/share/nexus/wordlists/common-paths.txt",
    "small": "/usr/share/nexus/wordlists/small-paths.txt",
}

_RESULT_LINE_RE = re.compile(
    r"^\s*\d+\s+L\s+(?P<lines>\d+)\s+W\s+(?P<words>\d+)\s+Ch\s+(?P<chars>\d+)\s+"
    r"(?P<code>\d+)\s+(?P<payload>.+)$"
)


async def run_wfuzz(
    base_url: str,
    wordlist: str = "common",
    hide_codes: str = "404",
    timeout_seconds: int = 300,
) -> tuple[ToolRunResult, list[dict] | None]:
    binary = require_binary("wfuzz")
    safe_url = assert_safe_url(base_url)

    if wordlist not in _ALLOWED_WORDLISTS:
        raise ValueError(f"Unknown wordlist profile: {wordlist!r}")
    wordlist_path = _ALLOWED_WORDLISTS[wordlist]

    target = safe_url.rstrip("/") + "/FUZZ"

    argv = [
        binary,
        "--hc", hide_codes,
        "-w", wordlist_path,
        "-z", "file",
        target,
    ]

    result = await run_command(argv, timeout_seconds=timeout_seconds)

    parsed: list[dict] = []
    for line in result.stdout.splitlines():
        m = _RESULT_LINE_RE.match(line)
        if m:
            parsed.append(
                {
                    "code": int(m.group("code")),
                    "lines": int(m.group("lines")),
                    "words": int(m.group("words")),
                    "chars": int(m.group("chars")),
                    "payload": m.group("payload").strip(),
                }
            )

    return result, parsed or None
