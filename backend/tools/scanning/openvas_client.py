"""
OpenVAS (Greenbone GVM) client — vulnerability *scanning* via the GMP
protocol, using the `gvm-cli` socket transport (part of gvm-tools).

This wrapper only creates scan targets/tasks and retrieves results/reports
through GMP — standard vulnerability-management operations. It does not
implement OpenVAS's credentialed "exploit verification" NVTs; those remain
disabled at the scan-config level (use a detection-only scan config such
as "Full and fast" without exploit verification, configured on the GVM
server side).
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from tools.base import ToolRunResult, require_binary, run_command
from utils.parser_utils import assert_safe_hostname_or_ip


@dataclass
class GvmFinding:
    name: str
    severity: float
    host: str
    port: str = ""
    description: str = ""
    nvt_oid: str = ""


def _gmp_command(xml_body: str) -> list[str]:
    binary = require_binary("gvm-cli")
    return [binary, "--gmp-username", "admin", "socket", "--xml", xml_body]


async def create_target(name: str, host: str, timeout_seconds: int = 30) -> str:
    """Create a GVM scan target, returning its target ID."""
    safe_host = assert_safe_hostname_or_ip(host)
    xml_body = (
        f'<create_target><name>{name}-{uuid.uuid4().hex[:6]}</name>'
        f'<hosts>{safe_host}</hosts></create_target>'
    )
    result = await run_command(_gmp_command(xml_body), timeout_seconds=timeout_seconds)
    root = ET.fromstring(result.stdout) if result.stdout.strip() else None
    return root.attrib.get("id", "") if root is not None else ""


async def create_and_start_task(
    target_id: str,
    scan_config_id: str,
    task_name: str,
    timeout_seconds: int = 30,
) -> str:
    """
    Create a scan task bound to a detection-oriented scan config (the
    `scan_config_id` should reference a non-exploit-verification config,
    e.g. GVM's built-in "Full and fast" config) and start it.
    Returns the task ID.
    """
    create_xml = (
        f'<create_task><name>{task_name}</name>'
        f'<target id="{target_id}"/><config id="{scan_config_id}"/></create_task>'
    )
    create_result = await run_command(_gmp_command(create_xml), timeout_seconds=timeout_seconds)
    root = ET.fromstring(create_result.stdout) if create_result.stdout.strip() else None
    task_id = root.attrib.get("id", "") if root is not None else ""

    if task_id:
        start_xml = f'<start_task task_id="{task_id}"/>'
        await run_command(_gmp_command(start_xml), timeout_seconds=timeout_seconds)

    return task_id


async def get_task_status(task_id: str, timeout_seconds: int = 30) -> dict:
    """Poll a task's status/progress."""
    xml_body = f'<get_tasks task_id="{task_id}"/>'
    result = await run_command(_gmp_command(xml_body), timeout_seconds=timeout_seconds)

    status, progress = "unknown", 0
    if result.stdout.strip():
        root = ET.fromstring(result.stdout)
        task_el = root.find(".//task")
        if task_el is not None:
            status_el = task_el.find("status")
            progress_el = task_el.find("progress")
            status = status_el.text if status_el is not None else "unknown"
            progress = int(progress_el.text) if progress_el is not None and progress_el.text else 0

    return {"task_id": task_id, "status": status, "progress": progress}


async def get_report_findings(report_id: str, timeout_seconds: int = 60) -> list[GvmFinding]:
    """Fetch and parse a completed scan's results into GvmFinding objects."""
    xml_body = f'<get_results report_id="{report_id}"/>'
    result = await run_command(_gmp_command(xml_body), timeout_seconds=timeout_seconds)

    findings: list[GvmFinding] = []
    if not result.stdout.strip():
        return findings

    root = ET.fromstring(result.stdout)
    for result_el in root.findall(".//result"):
        name_el = result_el.find("name")
        host_el = result_el.find("host")
        port_el = result_el.find("port")
        severity_el = result_el.find("severity")
        description_el = result_el.find("description")
        nvt_el = result_el.find("nvt")

        try:
            severity = float(severity_el.text) if severity_el is not None and severity_el.text else 0.0
        except ValueError:
            severity = 0.0

        findings.append(
            GvmFinding(
                name=name_el.text if name_el is not None else "",
                severity=severity,
                host=host_el.text if host_el is not None else "",
                port=port_el.text if port_el is not None else "",
                description=description_el.text if description_el is not None else "",
                nvt_oid=nvt_el.attrib.get("oid", "") if nvt_el is not None else "",
            )
        )

    return findings
