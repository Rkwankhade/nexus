"""
Scapy-based passive capture & analysis engine.

Scapy is a general-purpose packet manipulation library capable of crafting
and injecting arbitrary traffic (spoofing, ARP poisoning, custom exploit
packets, etc). This wrapper deliberately exposes only *passive* capabilities
— sniffing live interfaces or reading existing pcap files and summarizing
what's in them — and does not expose packet construction/sending. For
building and firing crafted packets, that capability is out of scope here.

Use pcap_analyzer.py (forensics layer) for offline analysis of files already
on disk; this module additionally supports short live-interface captures for
live triage.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from utils.logger import get_logger
from utils.parser_utils import utcnow_iso

log = get_logger(__name__)


@dataclass
class CaptureSummary:
    started_at: str
    finished_at: str
    packet_count: int
    protocol_counts: dict[str, int]
    top_talkers: list[tuple[str, int]]
    dns_queries: list[str]
    truncated: bool = False


def _summarize_packets(packets) -> CaptureSummary:
    from scapy.layers.inet import IP, TCP, UDP
    from scapy.layers.dns import DNSQR

    started_at = utcnow_iso()
    proto_counter: Counter[str] = Counter()
    talker_counter: Counter[str] = Counter()
    dns_queries: list[str] = []

    for pkt in packets:
        if pkt.haslayer(IP):
            src = pkt[IP].src
            talker_counter[src] += 1
            if pkt.haslayer(TCP):
                proto_counter["TCP"] += 1
            elif pkt.haslayer(UDP):
                proto_counter["UDP"] += 1
            else:
                proto_counter["IP-other"] += 1
        else:
            proto_counter["non-IP"] += 1

        if pkt.haslayer(DNSQR):
            try:
                qname = pkt[DNSQR].qname.decode(errors="replace")
                dns_queries.append(qname.rstrip("."))
            except Exception:
                pass

    return CaptureSummary(
        started_at=started_at,
        finished_at=utcnow_iso(),
        packet_count=len(packets),
        protocol_counts=dict(proto_counter),
        top_talkers=talker_counter.most_common(10),
        dns_queries=dns_queries[:100],
    )


def analyze_pcap_file(pcap_path: str, max_packets: int = 50_000) -> CaptureSummary:
    """Read an existing pcap/pcapng file and summarize its contents."""
    from scapy.utils import rdpcap

    packets = rdpcap(pcap_path, count=max_packets)
    summary = _summarize_packets(packets)
    summary.truncated = len(packets) >= max_packets
    return summary


def live_capture_summary(
    interface: str,
    duration_seconds: int = 30,
    max_packets: int = 5_000,
) -> CaptureSummary:
    """
    Passively sniff `interface` for up to `duration_seconds` (or until
    `max_packets` is reached) and return a traffic summary. Requires the
    backend process to have packet-capture privileges (e.g. CAP_NET_RAW).
    """
    from scapy.sendrecv import sniff

    duration_seconds = max(1, min(duration_seconds, 300))  # cap at 5 min
    packets = sniff(iface=interface, timeout=duration_seconds, count=max_packets, store=True)
    summary = _summarize_packets(packets)
    summary.truncated = len(packets) >= max_packets
    return summary
