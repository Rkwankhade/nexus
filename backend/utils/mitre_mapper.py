"""
MITRE ATT&CK technique tagging for findings and alerts.

This module maps finding/alert *categories* (as reported by scanners, SIEM
rules, or the AI triage engine) to MITRE ATT&CK technique IDs, purely for
labeling and reporting purposes (dashboards, PDF reports, SOC alert
enrichment). It does not contain attack instructions — only the
classification lookup used to tag defensive telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MitreTechnique:
    technique_id: str
    name: str
    tactic: str


# Curated subset of MITRE ATT&CK (Enterprise) techniques relevant to the
# finding/alert categories NEXUS's scanners and SIEM rules can produce.
_TECHNIQUE_CATALOG: dict[str, MitreTechnique] = {
    "T1046": MitreTechnique("T1046", "Network Service Discovery", "Discovery"),
    "T1595": MitreTechnique("T1595", "Active Scanning", "Reconnaissance"),
    "T1590": MitreTechnique("T1590", "Gather Victim Network Information", "Reconnaissance"),
    "T1589": MitreTechnique("T1589", "Gather Victim Identity Information", "Reconnaissance"),
    "T1592": MitreTechnique("T1592", "Gather Victim Host Information", "Reconnaissance"),
    "T1190": MitreTechnique("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "T1133": MitreTechnique("T1133", "External Remote Services", "Initial Access"),
    "T1078": MitreTechnique("T1078", "Valid Accounts", "Initial Access"),
    "T1110": MitreTechnique("T1110", "Brute Force", "Credential Access"),
    "T1552": MitreTechnique("T1552", "Unsecured Credentials", "Credential Access"),
    "T1040": MitreTechnique("T1040", "Network Sniffing", "Credential Access"),
    "T1557": MitreTechnique("T1557", "Adversary-in-the-Middle", "Credential Access"),
    "T1210": MitreTechnique("T1210", "Exploitation of Remote Services", "Lateral Movement"),
    "T1021": MitreTechnique("T1021", "Remote Services", "Lateral Movement"),
    "T1548": MitreTechnique("T1548", "Abuse Elevation Control Mechanism", "Privilege Escalation"),
    "T1068": MitreTechnique("T1068", "Exploitation for Privilege Escalation", "Privilege Escalation"),
    "T1499": MitreTechnique("T1499", "Endpoint Denial of Service", "Impact"),
    "T1486": MitreTechnique("T1486", "Data Encrypted for Impact", "Impact"),
    "T1105": MitreTechnique("T1105", "Ingress Tool Transfer", "Command and Control"),
    "T1071": MitreTechnique("T1071", "Application Layer Protocol", "Command and Control"),
    "T1059": MitreTechnique("T1059", "Command and Scripting Interpreter", "Execution"),
    "T1203": MitreTechnique("T1203", "Exploitation for Client Execution", "Execution"),
    "T1055": MitreTechnique("T1055", "Process Injection", "Defense Evasion"),
    "T1027": MitreTechnique("T1027", "Obfuscated Files or Information", "Defense Evasion"),
    "T1562": MitreTechnique("T1562", "Impair Defenses", "Defense Evasion"),
    "T1005": MitreTechnique("T1005", "Data from Local System", "Collection"),
    "T1041": MitreTechnique("T1041", "Exfiltration Over C2 Channel", "Exfiltration"),
    "T1119": MitreTechnique("T1119", "Automated Collection", "Collection"),
    "T1082": MitreTechnique("T1082", "System Information Discovery", "Discovery"),
    "T1087": MitreTechnique("T1087", "Account Discovery", "Discovery"),
}

# Keyword -> technique ID(s), used to auto-tag findings from free-text
# scanner output (e.g. nuclei template names, nikto messages, Suricata
# signature descriptions).
_KEYWORD_RULES: list[tuple[tuple[str, ...], list[str]]] = [
    (("open port", "service discovery", "port scan"), ["T1046"]),
    (("subdomain", "dns enumeration", "whois"), ["T1590"]),
    (("email harvest", "osint", "employee"), ["T1589", "T1592"]),
    (("sql injection", "rce", "remote code execution", "deserialization", "unauthenticated"), ["T1190"]),
    (("exposed rdp", "exposed ssh", "vpn", "remote service"), ["T1133"]),
    (("default credential", "weak password", "credential stuffing", "login brute"), ["T1110", "T1078"]),
    (("plaintext credential", "hardcoded secret", "leaked key", "exposed .env"), ["T1552"]),
    (("packet capture", "arp spoof", "mitm", "sniffing"), ["T1040", "T1557"]),
    (("smb relay", "pass the hash", "lateral movement"), ["T1210", "T1021"]),
    (("privilege escalation", "sudo misconfiguration", "suid"), ["T1068", "T1548"]),
    (("dos", "denial of service", "resource exhaustion"), ["T1499"]),
    (("ransomware", "encryption behavior"), ["T1486"]),
    (("beacon", "c2", "command and control", "suspicious outbound"), ["T1071", "T1105"]),
    (("powershell", "shell command", "script execution"), ["T1059"]),
    (("malicious document", "macro", "client-side exploit"), ["T1203"]),
    (("process injection", "code injection"), ["T1055"]),
    (("obfuscation", "packed binary", "encoded payload"), ["T1027"]),
    (("edr disabled", "av disabled", "log cleared", "defense evasion"), ["T1562"]),
    (("data staging", "local file collection"), ["T1005"]),
    (("exfiltration", "data transfer out"), ["T1041"]),
    (("system enumeration", "os fingerprint"), ["T1082"]),
    (("user enumeration", "account enumeration"), ["T1087"]),
]


def get_technique(technique_id: str) -> Optional[MitreTechnique]:
    return _TECHNIQUE_CATALOG.get(technique_id.upper())


def techniques_for_ids(technique_ids: list[str]) -> list[MitreTechnique]:
    return [t for tid in technique_ids if (t := get_technique(tid)) is not None]


def map_text_to_techniques(text: str) -> list[str]:
    """
    Given free-text describing a finding/alert (title + description),
    return the list of MITRE ATT&CK technique IDs whose keywords match.
    Used to auto-tag findings coming from tools that don't natively map
    to ATT&CK (nikto, nuclei, Suricata alert messages, etc).
    """
    if not text:
        return []

    lowered = text.lower()
    matched: list[str] = []
    for keywords, technique_ids in _KEYWORD_RULES:
        if any(kw in lowered for kw in keywords):
            for tid in technique_ids:
                if tid not in matched:
                    matched.append(tid)
    return matched


def build_kill_chain_summary(technique_ids: list[str]) -> dict[str, list[dict[str, str]]]:
    """
    Group a flat list of technique IDs by ATT&CK tactic, for rendering the
    "kill chain view" component on the frontend and in PDF reports.

    Returns: { "Initial Access": [{"id": "T1190", "name": "..."}], ... }
    """
    grouped: dict[str, list[dict[str, str]]] = {}
    for technique in techniques_for_ids(technique_ids):
        grouped.setdefault(technique.tactic, []).append(
            {"id": technique.technique_id, "name": technique.name}
        )
    return grouped
