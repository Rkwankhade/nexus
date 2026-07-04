"""
NEXUS — Neo4j graph database client.
Stores attack paths / attack graph nodes (hosts, services, findings,
credentials, exploits) and their relationships for the attack-graph
visualizer and AI-driven kill-chain reasoning.
"""
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from core.config import settings

_driver: Optional[AsyncDriver] = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


class Neo4jClient:
    def __init__(self) -> None:
        self.driver = get_driver()

    async def run_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            return [record.data() async for record in result]

    async def upsert_node(self, label: str, key: str, props: Dict[str, Any]) -> None:
        query = (
            f"MERGE (n:{label} {{key: $key}}) "
            f"SET n += $props RETURN n"
        )
        await self.run_query(query, {"key": key, "props": props})

    async def upsert_edge(
        self,
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        rel_type: str,
        props: Optional[Dict[str, Any]] = None,
    ) -> None:
        query = (
            f"MATCH (a:{from_label} {{key: $from_key}}), "
            f"(b:{to_label} {{key: $to_key}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            f"SET r += $props"
        )
        await self.run_query(
            query,
            {"from_key": from_key, "to_key": to_key, "props": props or {}},
        )

    async def get_graph_for_target(self, target_key: str) -> Dict[str, Any]:
        query = """
        MATCH (t:Target {key: $target_key})
        OPTIONAL MATCH path = (t)-[*0..4]-(n)
        WITH collect(DISTINCT t) + collect(DISTINCT n) AS nodes, path
        UNWIND nodes AS node
        WITH DISTINCT node, path
        RETURN collect(DISTINCT node) AS nodes,
               collect(DISTINCT relationships(path)) AS rel_paths
        """
        result = await self.run_query(query, {"target_key": target_key})
        return result[0] if result else {"nodes": [], "rel_paths": []}

    async def close(self) -> None:
        await self.driver.close()


neo4j_client = Neo4jClient()
