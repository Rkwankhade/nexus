"""
Suricata IDS manager — reads eve.json alert output and manages rule
enable/disable state + live rule reload via the `suricatasc` control
socket. This is IDS *detection* management (defensive telemetry), not an
attack tool.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tools.base import ToolRunResult, require_binary, run_command
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class SuricataAlert:
    timestamp: str
    src_ip: str
    src_port: Optional[int]
    dest_ip: str
    dest_port: Optional[int]
    proto: str
    signature: str
    signature_id: int
    category: str
    severity: int
    raw: dict = field(default_factory=dict)


def tail_eve_alerts(eve_json_path: str, since_byte_offset: int = 0, max_alerts: int = 500) -> tuple[list[SuricataAlert], int]:
    """
    Read new `event_type == alert` entries from a Suricata eve.json file
    starting at `since_byte_offset`. Returns (alerts, new_byte_offset) so
    the log_ingestor service can poll incrementally without re-reading the
    whole file each cycle.
    """
    path = Path(eve_json_path)
    if not path.exists():
        return [], since_byte_offset

    alerts: list[SuricataAlert] = []
    with path.open("r", errors="replace") as f:
        f.seek(since_byte_offset)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("event_type") != "alert":
                continue

            alert_data = event.get("alert", {})
            alerts.append(
                SuricataAlert(
                    timestamp=event.get("timestamp", ""),
                    src_ip=event.get("src_ip", ""),
                    src_port=event.get("src_port"),
                    dest_ip=event.get("dest_ip", ""),
                    dest_port=event.get("dest_port"),
                    proto=event.get("proto", ""),
                    signature=alert_data.get("signature", ""),
                    signature_id=alert_data.get("signature_id", 0),
                    category=alert_data.get("category", ""),
                    severity=alert_data.get("severity", 3),
                    raw=event,
                )
            )
            if len(alerts) >= max_alerts:
                break

        new_offset = f.tell()

    return alerts, new_offset


async def _suricatasc_command(command: str, socket_path: str = "/var/run/suricata/suricata-command.socket", timeout_seconds: int = 15) -> ToolRunResult:
    binary = require_binary("suricatasc")
    argv = [binary, "-c", command, socket_path]
    return await run_command(argv, timeout_seconds=timeout_seconds)


async def reload_rules(socket_path: str = "/var/run/suricata/suricata-command.socket") -> ToolRunResult:
    """Hot-reload Suricata's ruleset without restarting the process."""
    log.info("reloading Suricata rules")
    return await _suricatasc_command("reload-rules", socket_path)


async def get_suricata_status(socket_path: str = "/var/run/suricata/suricata-command.socket") -> dict:
    """Fetch uptime/capture-stats from the running Suricata instance."""
    result = await _suricatasc_command("uptime", socket_path)
    return {"raw": result.stdout, "succeeded": result.succeeded}


def disable_rule(sid: int, disable_conf_path: str = "/etc/suricata/disable.conf") -> None:
    """Add a signature ID to disable.conf (takes effect on next rule reload)."""
    path = Path(disable_conf_path)
    existing = path.read_text().splitlines() if path.exists() else []
    entry = str(sid)
    if entry not in existing:
        existing.append(entry)
        path.write_text("\n".join(existing) + "\n")
    log.info(f"disabled Suricata rule sid={sid}")


def enable_rule(sid: int, disable_conf_path: str = "/etc/suricata/disable.conf") -> None:
    """Remove a signature ID from disable.conf (re-enabling it on next reload)."""
    path = Path(disable_conf_path)
    if not path.exists():
        return
    existing = [line for line in path.read_text().splitlines() if line.strip() != str(sid)]
    path.write_text("\n".join(existing) + ("\n" if existing else ""))
    log.info(f"enabled Suricata rule sid={sid}")


def list_disabled_rules(disable_conf_path: str = "/etc/suricata/disable.conf") -> list[int]:
    path = Path(disable_conf_path)
    if not path.exists():
        return []
    sids: list[int] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.isdigit():
            sids.append(int(line))
    return sids
