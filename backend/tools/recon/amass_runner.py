"""
Amass wrapper — passive/active subdomain enumeration.

Only exposes Amass's `enum` subcommand (asset discovery). Passive mode is
the default since it queries public data sources (CT logs, DNS
aggregators) without touching the target infrastructure directly.
"""

from __future__ import annotations

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip, dedupe_preserve_order


async def run_amass_enum(
    domain: str,
    passive_only: bool = True,
    timeout_seconds: int = 600,
) -> tuple[ToolRunResult, list[str]]:
    """
    Enumerate subdomains for `domain`. Returns the raw tool result plus a
    deduped list of discovered subdomains parsed from stdout.
    """
    binary = require_binary("amass")
    safe_domain = assert_safe_hostname_or_ip(domain)

    argv = [binary, "enum", "-d", safe_domain]
    if passive_only:
        argv.append("-passive")

    result = await run_command(argv, timeout_seconds=timeout_seconds)

    subdomains = dedupe_preserve_order(
        line.strip() for line in result.stdout.splitlines() if line.strip().endswith(safe_domain)
    )
    return result, subdomains
