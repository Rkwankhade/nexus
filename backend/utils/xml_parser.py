"""
Nmap XML output parser.

Parses `nmap -oX` output into plain dataclasses/dicts that the recon tool
wrappers and scan-ingestion services can persist as Target/Finding rows.
This module only reads and structures scan results — it has no involvement
in constructing or issuing scan commands.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NmapPort:
    port: int
    protocol: str
    state: str
    service_name: str = ""
    product: str = ""
    version: str = ""
    extra_info: str = ""
    scripts: dict[str, str] = field(default_factory=dict)


@dataclass
class NmapHost:
    ip_address: str
    hostname: str = ""
    status: str = "unknown"
    os_match: str = ""
    os_accuracy: Optional[int] = None
    ports: list[NmapPort] = field(default_factory=list)


@dataclass
class NmapScanResult:
    scan_args: str
    start_time: str
    hosts: list[NmapHost] = field(default_factory=list)

    @property
    def host_count(self) -> int:
        return len(self.hosts)

    @property
    def open_port_count(self) -> int:
        return sum(
            1 for h in self.hosts for p in h.ports if p.state == "open"
        )


def parse_nmap_xml(xml_content: str) -> NmapScanResult:
    """
    Parse the XML string produced by `nmap -oX -` (or a file read into
    memory) into a structured NmapScanResult.

    Raises ET.ParseError if the content is not valid XML.
    """
    root = ET.fromstring(xml_content)

    result = NmapScanResult(
        scan_args=root.attrib.get("args", ""),
        start_time=root.attrib.get("startstr", ""),
    )

    for host_el in root.findall("host"):
        status_el = host_el.find("status")
        status = status_el.attrib.get("state", "unknown") if status_el is not None else "unknown"

        address_el = host_el.find("address")
        ip_address = address_el.attrib.get("addr", "") if address_el is not None else ""

        hostname = ""
        hostnames_el = host_el.find("hostnames")
        if hostnames_el is not None:
            hostname_el = hostnames_el.find("hostname")
            if hostname_el is not None:
                hostname = hostname_el.attrib.get("name", "")

        os_match = ""
        os_accuracy: Optional[int] = None
        os_el = host_el.find("os")
        if os_el is not None:
            osmatch_el = os_el.find("osmatch")
            if osmatch_el is not None:
                os_match = osmatch_el.attrib.get("name", "")
                accuracy_str = osmatch_el.attrib.get("accuracy")
                os_accuracy = int(accuracy_str) if accuracy_str else None

        host = NmapHost(
            ip_address=ip_address,
            hostname=hostname,
            status=status,
            os_match=os_match,
            os_accuracy=os_accuracy,
        )

        ports_el = host_el.find("ports")
        if ports_el is not None:
            for port_el in ports_el.findall("port"):
                state_el = port_el.find("state")
                state = state_el.attrib.get("state", "unknown") if state_el is not None else "unknown"

                service_el = port_el.find("service")
                service_name = product = version = extra_info = ""
                if service_el is not None:
                    service_name = service_el.attrib.get("name", "")
                    product = service_el.attrib.get("product", "")
                    version = service_el.attrib.get("version", "")
                    extra_info = service_el.attrib.get("extrainfo", "")

                scripts: dict[str, str] = {}
                for script_el in port_el.findall("script"):
                    script_id = script_el.attrib.get("id", "")
                    script_output = script_el.attrib.get("output", "")
                    if script_id:
                        scripts[script_id] = script_output

                host.ports.append(
                    NmapPort(
                        port=int(port_el.attrib.get("portid", 0)),
                        protocol=port_el.attrib.get("protocol", "tcp"),
                        state=state,
                        service_name=service_name,
                        product=product,
                        version=version,
                        extra_info=extra_info,
                        scripts=scripts,
                    )
                )

        result.hosts.append(host)

    return result


def nmap_result_to_dict(result: NmapScanResult) -> dict:
    """Serialize an NmapScanResult to a plain dict (for JSONB storage)."""
    return {
        "scan_args": result.scan_args,
        "start_time": result.start_time,
        "host_count": result.host_count,
        "open_port_count": result.open_port_count,
        "hosts": [
            {
                "ip_address": h.ip_address,
                "hostname": h.hostname,
                "status": h.status,
                "os_match": h.os_match,
                "os_accuracy": h.os_accuracy,
                "ports": [
                    {
                        "port": p.port,
                        "protocol": p.protocol,
                        "state": p.state,
                        "service_name": p.service_name,
                        "product": p.product,
                        "version": p.version,
                        "extra_info": p.extra_info,
                        "scripts": p.scripts,
                    }
                    for p in h.ports
                ],
            }
            for h in result.hosts
        ],
    }
