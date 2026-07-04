"""
PCAP analyzer — post-capture forensic analysis of packet captures using
pyshark (tshark bindings). Distinct from tools/network/wireshark_parser.py
which handles live-facing summaries; this module focuses on IR-style
artifact extraction: conversation summaries, DNS queries, HTTP requests,
credential-adjacent cleartext protocol usage, and suspicious beaconing
patterns for an analyst to review.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pyshark

from utils.logger import get_logger

log = get_logger(__name__)

_CLEARTEXT_PROTOCOLS = {"http", "ftp", "telnet", "smtp", "pop", "imap"}


@dataclass
class ConversationSummary:
    src: str
    dst: str
    protocol: str
    packet_count: int
    byte_count: int


@dataclass
class PcapAnalysisResult:
    file_path: str
    total_packets: int = 0
    protocol_counts: dict[str, int] = field(default_factory=dict)
    dns_queries: list[str] = field(default_factory=list)
    http_requests: list[dict] = field(default_factory=list)
    top_talkers: list[ConversationSummary] = field(default_factory=list)
    cleartext_protocol_hits: dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


class PcapNotFoundError(FileNotFoundError):
    pass


def _assert_pcap_exists(pcap_path: str) -> str:
    path = Path(pcap_path)
    if not path.exists() or not path.is_file():
        raise PcapNotFoundError(f"PCAP file not found: {pcap_path}")
    return str(path)


async def analyze_pcap(
    pcap_path: str,
    *,
    max_packets: int = 50_000,
    display_filter: Optional[str] = None,
) -> PcapAnalysisResult:
    """
    Parse a PCAP/PCAPNG file and produce a high-level forensic summary.
    This is read-only analysis of an existing capture file — it does not
    perform any live capture or network interaction.
    """
    path = _assert_pcap_exists(pcap_path)
    result = PcapAnalysisResult(file_path=path)

    protocol_counter: Counter[str] = Counter()
    conversation_bytes: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    conversation_packets: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    dns_queries: list[str] = []
    http_requests: list[dict] = []
    cleartext_counter: Counter[str] = Counter()

    try:
        capture = pyshark.FileCapture(
            path,
            display_filter=display_filter,
            keep_packets=False,
        )

        packet_count = 0
        for packet in capture:
            packet_count += 1
            if packet_count > max_packets:
                log.warning(f"pcap analysis hit max_packets={max_packets} cap; stopping early")
                break

            highest_layer = getattr(packet, "highest_layer", "UNKNOWN")
            protocol_counter[highest_layer] += 1

            try:
                length = int(getattr(packet, "length", 0))
            except (TypeError, ValueError):
                length = 0

            if hasattr(packet, "ip"):
                src, dst = packet.ip.src, packet.ip.dst
                transport = getattr(packet, "transport_layer", None) or "IP"
                key = (src, dst, transport)
                conversation_bytes[key] += length
                conversation_packets[key] += 1

            layer_names = {layer.layer_name for layer in packet.layers}
            for proto in _CLEARTEXT_PROTOCOLS & layer_names:
                cleartext_counter[proto] += 1

            if "dns" in layer_names:
                query_name = getattr(packet.dns, "qry_name", None)
                if query_name:
                    dns_queries.append(query_name)

            if "http" in layer_names and hasattr(packet.http, "request_method"):
                http_requests.append(
                    {
                        "method": getattr(packet.http, "request_method", ""),
                        "host": getattr(packet.http, "host", ""),
                        "uri": getattr(packet.http, "request_uri", ""),
                        "user_agent": getattr(packet.http, "user_agent", ""),
                    }
                )

        capture.close()
        result.total_packets = packet_count

    except Exception as exc:  # pyshark/tshark surfaces various runtime errors
        log.error(f"pcap analysis failed for {path}: {exc}")
        result.error = str(exc)
        return result

    top_talkers = sorted(
        (
            ConversationSummary(src=src, dst=dst, protocol=proto, packet_count=conversation_packets[key], byte_count=total)
            for key, total in conversation_bytes.items()
            for src, dst, proto in [key]
        ),
        key=lambda c: c.byte_count,
        reverse=True,
    )[:25]

    result.protocol_counts = dict(protocol_counter.most_common())
    result.dns_queries = sorted(set(dns_queries))
    result.http_requests = http_requests[:500]
    result.top_talkers = top_talkers
    result.cleartext_protocol_hits = dict(cleartext_counter)

    return result


async def extract_dns_queries(pcap_path: str, max_packets: int = 50_000) -> list[str]:
    """Convenience helper: return only the unique DNS query names seen in a capture."""
    analysis = await analyze_pcap(pcap_path, max_packets=max_packets, display_filter="dns")
    return analysis.dns_queries
