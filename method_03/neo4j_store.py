"""Persistencia e execucao Neo4j para o Metodo 03."""

from __future__ import annotations

from typing import Any

from method_01.graph_builder import GraphBuildResult, build_graph
from method_01.ontology import NODE_TYPES, RELATIONSHIP_TYPES
from method_03.settings import Neo4jSettings, get_neo4j_settings


METHOD_SOURCE = "method_03"
DOMAIN_NODE_LABEL = "GraphNode"


def get_driver(settings: Neo4jSettings | None = None):
    try:
        from neo4j import GraphDatabase
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependencia ausente: instale neo4j para usar o Metodo 03.") from exc

    settings = settings or get_neo4j_settings()
    return GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password))


def prepare_graph_payload() -> GraphBuildResult:
    return build_graph()


def create_schema(session) -> None:
    session.run(
        "CREATE CONSTRAINT graph_node_id IF NOT EXISTS "
        "FOR (n:GraphNode) REQUIRE n.node_id IS UNIQUE"
    )
    for node_type, spec in NODE_TYPES.items():
        session.run(
            f"CREATE CONSTRAINT method03_{node_type.lower()}_{spec.key_property}_unique "
            f"IF NOT EXISTS FOR (n:{safe_label(node_type)}) "
            f"REQUIRE n.{safe_property(spec.key_property)} IS UNIQUE"
        )


def reset_method_03_data(session) -> None:
    session.run(
        "MATCH (n) WHERE n.source_system = $source_system DETACH DELETE n",
        source_system=METHOD_SOURCE,
    )


def ingest_graph_to_neo4j(
    result: GraphBuildResult,
    *,
    settings: Neo4jSettings,
    reset: bool = False,
) -> dict[str, int]:
    driver = get_driver(settings)
    try:
        with driver.session(database=settings.database) as session:
            create_schema(session)
            if reset:
                reset_method_03_data(session)

            for node in result.nodes:
                session.run(
                    upsert_node_query(node.type),
                    node_id=node.id,
                    graph_key=node.key,
                    graph_type=node.type,
                    source_system=METHOD_SOURCE,
                    properties=sanitize_properties(node.properties),
                )

            for edge in result.edges:
                session.run(
                    upsert_edge_query(edge.type),
                    edge_id=edge.id,
                    source_id=edge.source,
                    target_id=edge.target,
                    graph_type=edge.type,
                    provenance=edge.provenance,
                    source_system=METHOD_SOURCE,
                    properties=sanitize_properties(edge.properties),
                )

            return {"nodes": len(result.nodes), "edges": len(result.edges)}
    finally:
        driver.close()


def run_explain(session, cypher: str, parameters: dict[str, Any]) -> None:
    session.run(f"EXPLAIN {cypher}", **parameters).consume()


def run_read_query(
    cypher: str,
    parameters: dict[str, Any],
    *,
    settings: Neo4jSettings | None = None,
) -> list[dict[str, Any]]:
    settings = settings or get_neo4j_settings()
    driver = get_driver(settings)
    try:
        with driver.session(database=settings.database) as session:
            run_explain(session, cypher, parameters)
            return session.run(cypher, **parameters).data()
    finally:
        driver.close()


def inspect_counts(session) -> dict[str, Any]:
    node_counts = session.run(
        """
        MATCH (n:GraphNode)
        WHERE n.source_system = $source_system
        RETURN labels(n) AS labels, count(*) AS count
        ORDER BY labels
        """,
        source_system=METHOD_SOURCE,
    ).data()
    relationship_counts = session.run(
        """
        MATCH ()-[r]->()
        WHERE r.source_system = $source_system
        RETURN type(r) AS type, count(*) AS count
        ORDER BY type
        """,
        source_system=METHOD_SOURCE,
    ).data()
    return {
        "node_counts": node_counts,
        "relationship_counts": relationship_counts,
    }


def upsert_node_query(node_type: str) -> str:
    label = safe_label(node_type)
    key_property = safe_property(NODE_TYPES[node_type].key_property)
    return (
        f"MERGE (n:GraphNode:{label} {{node_id: $node_id}}) "
        f"SET n.{key_property} = $graph_key, "
        "n.graph_key = $graph_key, "
        "n.graph_type = $graph_type, "
        "n.source_system = $source_system, "
        "n += $properties"
    )


def upsert_edge_query(edge_type: str) -> str:
    relationship_type = safe_relationship(edge_type)
    return (
        "MATCH (source:GraphNode {node_id: $source_id}) "
        "MATCH (target:GraphNode {node_id: $target_id}) "
        f"MERGE (source)-[r:{relationship_type} {{edge_id: $edge_id}}]->(target) "
        "SET r.graph_type = $graph_type, "
        "r.provenance = $provenance, "
        "r.source_system = $source_system, "
        "r += $properties"
    )


def sanitize_properties(properties: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in properties.items():
        if value is None:
            continue
        sanitized[safe_property(key)] = value
    return sanitized


def safe_label(value: str) -> str:
    if value not in NODE_TYPES and value != DOMAIN_NODE_LABEL:
        raise ValueError(f"Label nao permitida: {value}")
    return value


def safe_relationship(value: str) -> str:
    if value not in RELATIONSHIP_TYPES:
        raise ValueError(f"Relacionamento nao permitido: {value}")
    return value


def safe_property(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Propriedade Neo4j invalida: {value}")
    return value
