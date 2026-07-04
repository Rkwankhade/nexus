"""
WHOIS lookup wrapper — registrar/registration metadata for a domain.
Read-only public-record lookup.
"""

from __future__ import annotations

import re

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip

_FIELD_PATTERNS = {
    "registrar": r"Registrar:\s*(.+)",
    "creation_date": r"Creation Date:\s*(.+)",
    "expiration_date": r"(?:Registry Expiry Date|Expiration Date):\s*(.+)",
    "updated_date": r"Updated Date:\s*(.+)",
    "name_servers": r"Name Server:\s*(.+)",
    "status": r"Domain Status:\s*(.+)",
    "org": r"Registrant Organization:\s*(.+)",
    "country": r"Registrant Country:\s*(.+)",
}


async def run_whois(domain: str, timeout_seconds: int = 30) -> tuple[ToolRunResult, dict]:
    """Run whois against `domain` and return (raw_result, parsed_fields)."""
    binary = require_binary("whois")
    safe_domain = assert_safe_hostname_or_ip(domain)

    result = await run_command([binary, safe_domain], timeout_seconds=timeout_seconds)

    parsed: dict[str, object] = {}
    for field_name, pattern in _FIELD_PATTERNS.items():
        matches = re.findall(pattern, result.stdout, re.IGNORECASE)
        if not matches:
            continue
        cleaned = [m.strip() for m in matches]
        parsed[field_name] = cleaned if field_name in ("name_servers", "status") else cleaned[0]

    return result, parsed
