"""
dnsx wrapper — fast DNS resolution/record enumeration for a list of hosts.
Passive/low-impact: performs standard DNS queries only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip, parse_json_lines


@dataclass
class DnsxRecord:
    host: str
    a_records: list[str] = field(default_factory=list)
    aaaa_records: list[str] = field(default_factory=list)
    cname_records: list[str] = field(default_factory=list)
    mx_records: list[str] = field(default_factory=list)
    txt_records: list[str] = field(default_factory=list)
    ns_records: list[str] = field(default_factory=list)
    status_code: str = ""


async def run_dnsx(
    hosts: list[str],
    timeout_seconds: int = 120,
) -> tuple[ToolRunResult, list[DnsxRecord]]:
    """
    Resolve A/AAAA/CNAME/MX/TXT/NS records for each host in `hosts` using
    dnsx's JSON output mode. Input is piped via stdin so no target list is
    ever placed on the argv/command line.
    """
    binary = require_binary("dnsx")
    safe_hosts = [assert_safe_hostname_or_ip(h) for h in hosts]

    argv = [
        binary, "-silent", "-json",
        "-a", "-aaaa", "-cname", "-mx", "-txt", "-ns",
    ]

    import asyncio
    from utils.parser_utils import truncate_output, utcnow_iso

    started_at = utcnow_iso()
    loop = asyncio.get_event_loop()
    started = loop.time()

    process = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    input_data = ("\n".join(safe_hosts) + "\n").encode()

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(input=input_data), timeout=timeout_seconds
        )
        timed_out = False
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        stdout_bytes, stderr_bytes, timed_out = b"", b"", True

    finished = loop.time()
    stdout_text = truncate_output(stdout_bytes.decode(errors="replace"))
    stderr_text = truncate_output(stderr_bytes.decode(errors="replace"))

    result = ToolRunResult(
        tool=binary,
        command=argv,
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=stdout_text,
        stderr=stderr_text,
        timed_out=timed_out,
        started_at=started_at,
        finished_at=utcnow_iso(),
        duration_seconds=round(finished - started, 2),
    )

    records: list[DnsxRecord] = []
    for obj in parse_json_lines(stdout_text):
        records.append(
            DnsxRecord(
                host=obj.get("host", ""),
                a_records=obj.get("a", []) or [],
                aaaa_records=obj.get("aaaa", []) or [],
                cname_records=obj.get("cname", []) or [],
                mx_records=obj.get("mx", []) or [],
                txt_records=obj.get("txt", []) or [],
                ns_records=obj.get("ns", []) or [],
                status_code=obj.get("status_code", ""),
            )
        )

    return result, records
