"""
PCAP parsing via tshark (Wireshark's CLI component) — read-only traffic
analysis for forensics/incident-response workflows. This module only
reads existing capture files; it has no packet-injection or live-capture
capability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from tools.base import ToolRunResult, require_binary, run_command


@dataclass
class PacketSummary:
    number: int
    timestamp: str
    src_ip: str
    dst_ip: str
    protocol: str
    length: int
    info: str = ""


@dataclass
class PcapSummary:
    packet_count: int
    duration_seconds: float
    protocols: dict[str, int] = field(default_factory=dict)
    top_talkers: dict[str, int] = field(default_factory=dict)
    dns_queries: list[str] = field(default_factory=list)
    http_hosts: list[str] = field(default_factory=list)


async def parse_pcap_summary(pcap_path: str, timeout_seconds: int = 300) -> tuple[ToolRunResult, PcapSummary]:
    """
    Produce a high-level summary of a capture file: protocol breakdown,
    top talkers by packet count, DNS queries seen, and HTTP Host headers
    seen. Used to populate the forensics dashboard's PCAP overview.
    """
    binary = require_binary("tshark")
    path = Path(pcap_path)
    if not path.exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

    # Protocol hierarchy stats
    proto_argv = [binary, "-r", str(path), "-q", "-z", "io,phs"]
    proto_result = await run_command(proto_argv, timeout_seconds=timeout_seconds)
    protocols = _parse_protocol_hierarchy(proto_result.stdout)

    # Conversations (top talkers)
    conv_argv = [binary, "-r", str(path), "-q", "-z", "conv,ip"]
    conv_result = await run_command(conv_argv, timeout_seconds=timeout_seconds)
    top_talkers = _parse_conversations(conv_result.stdout)

    # DNS queries
    dns_argv = [binary, "-r", str(path), "-Y", "dns.flags.response == 0", "-T", "fields", "-e", "dns.qry.name"]
    dns_result = await run_command(dns_argv, timeout_seconds=timeout_seconds)
    dns_queries = sorted(set(line.strip() for line in dns_result.stdout.splitlines() if line.strip()))

    # HTTP Host headers
    http_argv = [binary, "-r", str(path), "-Y", "http.request", "-T", "fields", "-e", "http.host"]
    http_result = await run_command(http_argv, timeout_seconds=timeout_seconds)
    http_hosts = sorted(set(line.strip() for line in http_result.stdout.splitlines() if line.strip()))

    # Packet count + duration
    count_argv = [binary, "-r", str(path), "-q", "-z", "io,stat,0"]
    count_result = await run_command(count_argv, timeout_seconds=timeout_seconds)
    packet_count, duration = _parse_io_stat(count_result.stdout)

    summary = PcapSummary(
        packet_count=packet_count,
        duration_seconds=duration,
        protocols=protocols,
        top_talkers=top_talkers,
        dns_queries=dns_queries[:200],
        http_hosts=http_hosts[:200],
    )

    return proto_result, summary


async def extract_packets_json(
    pcap_path: str,
    display_filter: str = "",
    max_packets: int = 500,
    timeout_seconds: int = 300,
) -> tuple[ToolRunResult, list[PacketSummary]]:
    """Extract a bounded list of packets (optionally filtered) as structured rows for the UI packet table."""
    binary = require_binary("tshark")
    path = Path(pcap_path)
    if not path.exists():
        raise FileNotFoundError(f"PCAP file not found: {pcap_path}")

    argv = [
        binary, "-r", str(path),
        "-T", "json",
        "-c", str(max_packets),
    ]
    if display_filter:
        argv += ["-Y", display_filter]

    result = await run_command(argv, timeout_seconds=timeout_seconds)

    packets: list[PacketSummary] = []
    try:
        raw_packets = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        raw_packets = []

    for idx, pkt in enumerate(raw_packets, start=1):
        layers = pkt.get("_source", {}).get("layers", {})
        frame = layers.get("frame", {})
        ip_layer = layers.get("ip", {})

        packets.append(
            PacketSummary(
                number=idx,
                timestamp=frame.get("frame.time", ""),
                src_ip=ip_layer.get("ip.src", ""),
                dst_ip=ip_layer.get("ip.dst", ""),
                protocol=frame.get("frame.protocols", "").split(":")[-1] if frame.get("frame.protocols") else "",
                length=int(frame.get("frame.len", 0) or 0),
            )
        )

    return result, packets


def _parse_protocol_hierarchy(output: str) -> dict[str, int]:
    protocols: dict[str, int] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith(("eth", "ip", "tcp", "udp", "http", "dns", "tls", "arp", "icmp")):
            continue
        parts = line.split()
        if len(parts) >= 2 and "frames:" in line:
            proto_name = parts[0]
            try:
                frame_count = int(line.split("frames:")[1].split()[0])
                protocols[proto_name] = frame_count
            except (IndexError, ValueError):
                continue
    return protocols


def _parse_conversations(output: str) -> dict[str, int]:
    talkers: dict[str, int] = {}
    in_table = False
    for line in output.splitlines():
        if line.strip().startswith("==="):
            in_table = not in_table
            continue
        if not in_table:
            continue
        parts = line.split()
        if len(parts) < 4 or "<->" not in line:
            continue
        try:
            src = parts[0]
            frames = int(parts[3])
            talkers[src] = talkers.get(src, 0) + frames
        except (IndexError, ValueError):
            continue
    return dict(sorted(talkers.items(), key=lambda kv: kv[1], reverse=True)[:20])


def _parse_io_stat(output: str) -> tuple[int, float]:
    packet_count = 0
    duration = 0.0
    for line in output.splitlines():
        if "Duration:" in line:
            try:
                duration = float(line.split("Duration:")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
        stripped = line.strip()
        if stripped.startswith("<") and "..." in stripped:
            try:
                packet_count += int(stripped.split()[1])
            except (IndexError, ValueError):
                continue
    return packet_count, duration
