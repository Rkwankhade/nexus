"""
Attack graph service — builds and queries a Neo4j graph representing a
target's discovered attack surface: hosts, open services, findings, and
credentials-at-risk, plus the relationships between them (HAS_SERVICE,
HAS_FINDING, AFFECTS, etc). This powers the react-flow visualizer on the
frontend so analysts can see exposure at a glance.

This is a graph of *what was discovered*, not a planned attack path — it
does not compute or suggest exploitation sequences. Nodes/edges are
derived directly from Scan/Finding/Target records already in Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.neo4j_client import neo4j_client
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class GraphNode:
    key: str
    label: str  # Neo4j node label: Target | Host | Service | Finding | Credential
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    from_key: str
    from_label: str
    to_key: str
    to_label: str
    rel_type: str
    properties: dict[str, Any] = field(default_factory=dict)


class AttackGraphService:
    async def upsert_target(self, target: Any) -> None:
        await neo4j_client.upsert_node(
            "Target",
            key=str(target.id),
            props={
                "name": target.name,
                "value": target.value,
                "type": getattr(target.type, "value", str(target.type)),
                "status": getattr(target.status, "value", str(target.status)),
            },
        )

    async def upsert_host(self, target_id: str, host: str) -> None:
        host_key = f"{target_id}:{host}"
        await neo4j_client.upsert_node("Host", key=host_key, props={"address": host})
        await neo4j_client.upsert_edge("Target", str(target_id), "Host", host_key, "HAS_HOST")

    async def upsert_service(self, target_id: str, host: str, port: int, service_name: str, banner: str = "") -> None:
        host_key = f"{target_id}:{host}"
        service_key = f"{host_key}:{port}"
        await neo4j_client.upsert_node(
            "Service",
            key=service_key,
            props={"port": port, "service_name": service_name, "banner": banner[:500]},
        )
        await neo4j_client.upsert_edge("Host", host_key, "Service", service_key, "EXPOSES")

    async def upsert_finding(self, target: Any, finding: Any) -> None:
        target_id = str(target.id)
        finding_key = str(finding.id)

        await self.upsert_target(target)

        await neo4j_client.upsert_node(
            "Finding",
            key=finding_key,
            props={
                "title": finding.title,
                "severity": getattr(finding.severity, "value", str(finding.severity)),
                "status": getattr(finding.status, "value", str(finding.status)),
                "cvss_score": finding.cvss_score,
                "cve_ids": finding.cve_ids or [],
                "source_tool": finding.source_tool,
            },
        )
        await neo4j_client.upsert_edge("Target", target_id, "Finding", finding_key, "HAS_FINDING")

        if finding.affected_host:
            host_key = f"{target_id}:{finding.affected_host}"
            await neo4j_client.upsert_node("Host", key=host_key, props={"address": finding.affected_host})
            await neo4j_client.upsert_edge("Target", target_id, "Host", host_key, "HAS_HOST")
            await neo4j_client.upsert_edge("Host", host_key, "Finding", finding_key, "HAS_FINDING")

            if finding.affected_port:
                service_key = f"{host_key}:{finding.affected_port}"
                await neo4j_client.upsert_node(
                    "Service",
                    key=service_key,
                    props={"port": finding.affected_port, "service_name": finding.affected_service or ""},
                )
                await neo4j_client.upsert_edge("Host", host_key, "Service", service_key, "EXPOSES")
                await neo4j_client.upsert_edge("Service", service_key, "Finding", finding_key, "HAS_FINDING")

    async def get_target_graph(self, target_id: str) -> dict[str, Any]:
        """Fetch the full graph rooted at a target for frontend rendering
        (react-flow expects a flat nodes[]/edges[] shape, built here)."""
        raw = await neo4j_client.get_graph_for_target(target_id)
        nodes_raw = raw.get("nodes", [])
        rel_paths_raw = raw.get("rel_paths", [])

        nodes = [
            {
                "id": n.get("key"),
                "label": list(n.labels)[0] if hasattr(n, "labels") else n.get("label", "Node"),
                "data": dict(n),
            }
            for n in nodes_raw
            if n is not None
        ]

        edges: list[dict[str, Any]] = []
        seen_edges: set[tuple] = set()
        for rel_group in rel_paths_raw:
            for rel in rel_group or []:
                if rel is None:
                    continue
                start_key = rel.start_node.get("key")
                end_key = rel.end_node.get("key")
                edge_id = (start_key, end_key, rel.type)
                if edge_id in seen_edges:
                    continue
                seen_edges.add(edge_id)
                edges.append({"source": start_key, "target": end_key, "type": rel.type})

        return {"nodes": nodes, "edges": edges}

    async def get_severity_exposure_summary(self, target_id: str) -> dict[str, int]:
        """Quick aggregate query for dashboard cards: count of findings by
        severity reachable from a target node in the graph."""
        query = """
        MATCH (t:Target {key: $target_id})-[:HAS_FINDING]->(f:Finding)
        RETURN f.severity AS severity, count(f) AS count
        """
        rows = await neo4j_client.run_query(query, {"target_id": target_id})
        return {row["severity"]: row["count"] for row in rows}


attack_graph_service = AttackGraphService()
