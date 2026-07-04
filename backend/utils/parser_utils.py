"""
Shared helpers for turning raw tool output (JSON lines, plain text, CSV-ish
formats) into normalized structures the rest of the backend can persist,
plus input-sanitization helpers used before any value is interpolated into
a subprocess command line.
"""

from __future__ import annotations

import ipaddress
import json
import re
import shlex
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# JSON-lines / text parsing
# ---------------------------------------------------------------------------


def parse_json_lines(raw_output: str) -> list[dict]:
    """
    Parse newline-delimited JSON (the output format used by nuclei, dnsx,
    and several other tools with `-json`/`-jsonl` flags). Lines that fail
    to parse are silently skipped rather than aborting the whole batch.
    """
    records: list[dict] = []
    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def parse_json_safe(raw_output: str) -> Optional[Any]:
    """Parse a single JSON document, returning None instead of raising."""
    try:
        return json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        return None


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI color/escape codes from CLI tool output before storage/display."""
    ansi_pattern = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_pattern.sub("", text)


def extract_lines_matching(text: str, pattern: str) -> list[str]:
    """Return all lines in `text` matching a regex pattern (case-insensitive)."""
    compiled = re.compile(pattern, re.IGNORECASE)
    return [line for line in text.splitlines() if compiled.search(line)]


def truncate_output(text: str, max_chars: int = 50_000) -> str:
    """Cap stored tool output size; keep head and tail so context isn't lost."""
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return f"{head}\n\n... [truncated {len(text) - max_chars} chars] ...\n\n{tail}"


# ---------------------------------------------------------------------------
# Host / URL normalization
# ---------------------------------------------------------------------------


def normalize_hostname(value: str) -> str:
    """Strip scheme, path, port, and trailing dot from a host-like string."""
    value = value.strip()
    if "://" in value:
        parsed = urlparse(value)
        value = parsed.hostname or value
    value = value.split(":")[0] if not is_ip_address(value) else value
    return value.rstrip(".").lower()


def is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_private_ip(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_private
    except ValueError:
        return False


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Input sanitization for subprocess invocation
# ---------------------------------------------------------------------------

_SAFE_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9.\-]+$")
_SAFE_URL_RE = re.compile(r"^https?://[a-zA-Z0-9.\-:/_?&=%#~+,;]+$")


class UnsafeInputError(ValueError):
    """Raised when user-supplied input fails validation before subprocess use."""


def assert_safe_hostname_or_ip(value: str) -> str:
    """
    Validate that `value` is a bare hostname or IP with no shell metacharacters,
    before it's passed as a CLI argument to a scanning tool. Raises
    UnsafeInputError on anything else (command chaining attempts, flags
    injection via leading `-`, etc).
    """
    value = value.strip()
    if not value or value.startswith("-"):
        raise UnsafeInputError(f"Invalid target: {value!r}")
    if not _SAFE_HOSTNAME_RE.match(value):
        raise UnsafeInputError(f"Target contains disallowed characters: {value!r}")
    return value


def assert_safe_url(value: str) -> str:
    value = value.strip()
    if not value or not _SAFE_URL_RE.match(value):
        raise UnsafeInputError(f"Invalid or unsafe URL: {value!r}")
    return value


def quote_arg(value: str) -> str:
    """Shell-quote a single argument (use when building display strings only —
    actual subprocess calls should use list-form args, never shell=True)."""
    return shlex.quote(value)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
