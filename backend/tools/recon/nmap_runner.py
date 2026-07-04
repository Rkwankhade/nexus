"""
Nmap recon wrapper — service/host discovery scans only.

Deliberately exposes only discovery/enumeration scan profiles (host
discovery, port scan, service/version detection, default NSE scripts).
It does not expose `--script vuln`/exploit-category NSE scripts or raw
flag pass-through, so this wrapper cannot be used to run Nmap's
exploitation scripts.
"""

from __future__ import annotations

import enum
import tempfile
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip
from utils.xml_parser import NmapScanResult, parse_nmap_xml


class ScanProfile(str, enum.Enum):
    PING_SWEEP = "ping_sweep"          # -sn
    QUICK = "quick"                    # -F -T4
    FULL_PORT = "full_port"            # -p- -T4
    SERVICE_VERSION = "service_version"  # -sV -sC -T4


_PROFILE_FLAGS: dict[ScanProfile, list[str]] = {
    ScanProfile.PING_SWEEP: ["-sn"],
    ScanProfile.QUICK: ["-F", "-T4"],
    ScanProfile.FULL_PORT: ["-p-", "-T4"],
    ScanProfile.SERVICE_VERSION: ["-sV", "-sC", "-T4"],
}


async def run_nmap_scan(
    target: str,
    profile: ScanProfile = ScanProfile.SERVICE_VERSION,
    timeout_seconds: int = 900,
) -> tuple[ToolRunResult, NmapScanResult | None]:
    """
    Run an Nmap discovery/enumeration scan against `target` and return the
    raw tool result plus the parsed structured result (None if parsing the
    XML output failed, e.g. the scan was killed by timeout).
    """
    binary = require_binary("nmap")
    safe_target = assert_safe_hostname_or_ip(target)

    with tempfile.TemporaryDirectory() as tmp_dir:
        xml_path = Path(tmp_dir) / "scan.xml"
        argv = [binary, *_PROFILE_FLAGS[profile], "-oX", str(xml_path), safe_target]

        result = await run_command(argv, timeout_seconds=timeout_seconds)

        parsed: NmapScanResult | None = None
        if xml_path.exists():
            try:
                parsed = parse_nmap_xml(xml_path.read_text(errors="replace"))
            except Exception:
                parsed = None

        return result, parsed
