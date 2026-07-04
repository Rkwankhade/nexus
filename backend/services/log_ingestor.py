"""
Log ingestor — normalizes incoming SIEM-adjacent log events (Suricata EVE
JSON, Wazuh alerts, syslog, firewall logs) into LogEntry records, runs them
through the Sigma detection engine, and raises Alert records + real-time
notifications on matches. This is the ingestion side of the blue-team
workflow; tools/blueteam/sigma_engine.py owns the actual rule matching.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.alert import Alert, AlertSeverity
from models.log_entry import LogEntry, LogSource
from services.notification_service import notification_service
from tools.blueteam.sigma_engine import (
    SigmaMatch,
    SigmaRule,
    evaluate_event_against_rules,
    load_rules_from_directory,
)
from utils.logger import get_logger
from utils.mitre_mapper import map_text_to_techniques

log = get_logger(__name__)

_rule_cache: Optional[list[SigmaRule]] = None


def _get_sigma_rules() -> list[SigmaRule]:
    """Lazily load and cache the Sigma rule set from disk. Call
    `reload_sigma_rules()` after adding/editing rule files at runtime."""
    global _rule_cache
    if _rule_cache is None:
        rules_dir = getattr(settings, "SIGMA_RULES_DIR", "/data/sigma_rules")
        try:
            _rule_cache = load_rules_from_directory(rules_dir)
            log.info(f"loaded {len(_rule_cache)} Sigma rules from {rules_dir}")
        except FileNotFoundError:
            log.warning(f"Sigma rules directory not found at {rules_dir}; no rules loaded")
            _rule_cache = []
    return _rule_cache


def reload_sigma_rules() -> int:
    global _rule_cache
    _rule_cache = None
    return len(_get_sigma_rules())

_SOURCE_KEY_MAP = {
    "suricata": LogSource.SURICATA,
    "wazuh": LogSource.WAZUH,
    "syslog": LogSource.SYSLOG,
    "firewall": LogSource.FIREWALL,
    "auth": LogSource.AUTH,
}


@dataclass
class IngestResult:
    ingested_count: int = 0
    alerts_raised: int = 0
    errors: list[str] = field(default_factory=list)


def _normalize_suricata_event(raw: dict) -> dict:
    return {
        "host": raw.get("src_ip", ""),
        "event_type": raw.get("event_type", "suricata_event"),
        "severity": (raw.get("alert", {}) or {}).get("severity_label", "info"),
        "message": (raw.get("alert", {}) or {}).get("signature", json.dumps(raw)[:500]),
    }


def _normalize_wazuh_event(raw: dict) -> dict:
    rule = raw.get("rule", {}) or {}
    return {
        "host": raw.get("agent", {}).get("name", "") if isinstance(raw.get("agent"), dict) else "",
        "event_type": rule.get("description", "wazuh_alert"),
        "severity": _wazuh_level_to_severity(rule.get("level", 0)),
        "message": rule.get("description", json.dumps(raw)[:500]),
    }


def _wazuh_level_to_severity(level: Any) -> str:
    try:
        level = int(level)
    except (TypeError, ValueError):
        return "info"
    if level >= 12:
        return "critical"
    if level >= 8:
        return "high"
    if level >= 4:
        return "medium"
    return "low"


def _normalize_generic_event(raw: dict) -> dict:
    return {
        "host": raw.get("host", raw.get("hostname", "")),
        "event_type": raw.get("event_type", "log_event"),
        "severity": raw.get("severity", "info"),
        "message": raw.get("message", json.dumps(raw)[:500]),
    }


_NORMALIZERS = {
    LogSource.SURICATA: _normalize_suricata_event,
    LogSource.WAZUH: _normalize_wazuh_event,
}


async def ingest_events(
    db: AsyncSession,
    source: str,
    raw_events: list[dict],
    *,
    broadcast_alerts: bool = True,
) -> IngestResult:
    """
    Normalize and persist a batch of raw log events from a given source,
    running each through the Sigma engine and raising Alert records for
    matches. Intended to be called from the SIEM webhook/ingest endpoint
    or a scheduled log-tailing worker task.
    """
    result = IngestResult()
    log_source = _SOURCE_KEY_MAP.get(source.lower(), LogSource.CUSTOM)
    normalizer = _NORMALIZERS.get(log_source, _normalize_generic_event)

    for raw_event in raw_events:
        try:
            normalized = normalizer(raw_event)
            matches: list[SigmaMatch] = evaluate_event_against_rules(raw_event, _get_sigma_rules())

            entry = LogEntry(
                source=log_source,
                host=normalized["host"],
                event_type=normalized["event_type"],
                severity=normalized["severity"],
                message=normalized["message"],
                raw=raw_event,
                matched_rules=[m.rule.rule_id for m in matches],
            )
            db.add(entry)
            await db.flush()  # populate entry.id without committing yet

            result.ingested_count += 1

            for match in matches:
                alert = await _raise_alert_from_match(db, entry, match, broadcast_alerts)
                if alert:
                    result.alerts_raised += 1

        except Exception as exc:
            log.warning(f"failed to ingest log event from {source}: {exc}")
            result.errors.append(str(exc))

    await db.commit()
    return result


async def _raise_alert_from_match(
    db: AsyncSession,
    entry: LogEntry,
    match: "SigmaMatch",
    broadcast: bool,
) -> Optional[Alert]:
    rule = match.rule
    severity = _sigma_level_to_alert_severity(rule.level)
    mitre_techniques = [t for t in rule.tags if t.lower().startswith("attack.t")] or map_text_to_techniques(rule.title)
    alert = Alert(
        title=rule.title,
        description=f"Sigma rule '{rule.rule_id}' matched log entry on host {entry.host}: {entry.message[:300]}",
        severity=severity,
        source=entry.source.value if hasattr(entry.source, "value") else str(entry.source),
        rule_id=rule.rule_id,
        mitre_techniques=mitre_techniques,
        related_log_ids=[str(entry.id)],
        raw={"log_entry_id": str(entry.id), "sigma_rule": rule.rule_id},
    )
    db.add(alert)
    await db.flush()

    if broadcast:
        await notification_service.push_new_alert(str(alert.id), severity.value, alert.title)

    return alert


def _sigma_level_to_alert_severity(level: str) -> AlertSeverity:
    mapping = {
        "critical": AlertSeverity.CRITICAL,
        "high": AlertSeverity.HIGH,
        "medium": AlertSeverity.MEDIUM,
        "low": AlertSeverity.LOW,
    }
    return mapping.get((level or "medium").lower(), AlertSeverity.MEDIUM)
