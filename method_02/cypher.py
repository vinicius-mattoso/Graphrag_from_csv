"""Cypher controlado para ingestao e recuperacao do Metodo 02."""

from __future__ import annotations

from typing import Any

from method_01.ontology import NODE_TYPES, RELATIONSHIP_TYPES
from method_02.settings import Neo4jSettings


METHOD_SOURCE = "method_02"
DOCUMENT_LABEL = "GraphDocument"
DOMAIN_NODE_LABEL = "GraphNode"


def constraint_queries() -> list[str]:
    queries = [
        (
            "CREATE CONSTRAINT graph_node_id IF NOT EXISTS "
            "FOR (n:GraphNode) REQUIRE n.node_id IS UNIQUE"
        ),
        (
            "CREATE CONSTRAINT graph_document_doc_id IF NOT EXISTS "
            "FOR (d:GraphDocument) REQUIRE d.doc_id IS UNIQUE"
        ),
    ]
    for node_type, spec in NODE_TYPES.items():
        queries.append(
            f"CREATE CONSTRAINT {node_type.lower()}_{spec.key_property}_unique IF NOT EXISTS "
            f"FOR (n:{safe_label(node_type)}) REQUIRE n.{safe_property(spec.key_property)} IS UNIQUE"
        )
    return queries


def index_queries(settings: Neo4jSettings) -> list[str]:
    vector_index_name = safe_identifier(settings.vector_index_name)
    fulltext_index_name = safe_identifier(settings.fulltext_index_name)
    return [
        (
            f"CREATE FULLTEXT INDEX {fulltext_index_name} IF NOT EXISTS "
            "FOR (d:GraphDocument) ON EACH [d.page_content]"
        ),
        (
            f"CREATE VECTOR INDEX {vector_index_name} IF NOT EXISTS "
            "FOR (d:GraphDocument) ON (d.embedding) "
            "OPTIONS {indexConfig: {"
            f"`vector.dimensions`: {settings.embedding_dimension}, "
            "`vector.similarity_function`: 'cosine'"
            "}}"
        ),
    ]


def reset_query() -> str:
    return (
        "MATCH (n) WHERE n.source_system = $source_system "
        "DETACH DELETE n"
    )


def upsert_node_query(node_type: str) -> str:
    if node_type not in NODE_TYPES:
        raise ValueError(f"Tipo de no fora da ontologia: {node_type}")
    key_property = safe_property(NODE_TYPES[node_type].key_property)
    label = safe_label(node_type)
    return (
        f"MERGE (n:GraphNode:{label} {{node_id: $node_id}}) "
        f"SET n.{key_property} = $graph_key, "
        "n.graph_type = $graph_type, "
        "n.graph_key = $graph_key, "
        "n.source_system = $source_system, "
        "n += $properties"
    )


def upsert_edge_query(edge_type: str) -> str:
    if edge_type not in RELATIONSHIP_TYPES:
        raise ValueError(f"Relacionamento fora da ontologia: {edge_type}")
    rel_type = safe_relationship(edge_type)
    return (
        "MATCH (source:GraphNode {node_id: $source_id}) "
        "MATCH (target:GraphNode {node_id: $target_id}) "
        f"MERGE (source)-[r:{rel_type} {{edge_id: $edge_id}}]->(target) "
        "SET r.graph_type = $graph_type, "
        "r.provenance = $provenance, "
        "r.source_system = $source_system, "
        "r += $properties"
    )


def upsert_document_query() -> str:
    return (
        "MERGE (d:GraphDocument {doc_id: $doc_id}) "
        "SET d.page_content = $page_content, "
        "d.embedding = $embedding, "
        "d.source_system = $source_system, "
        "d += $metadata"
    )


def upsert_document_link_query(relationship_type: str) -> str:
    rel_type = safe_relationship(relationship_type)
    return (
        "MATCH (d:GraphDocument {doc_id: $doc_id}) "
        "MATCH (n:GraphNode {node_id: $node_id}) "
        f"MERGE (d)-[r:{rel_type}]->(n) "
        "SET r.source_system = $source_system"
    )


def vector_search_query(settings: Neo4jSettings) -> str:
    index_name = safe_identifier(settings.vector_index_name)
    return (
        f"CALL db.index.vector.queryNodes('{index_name}', $k, $embedding) "
        "YIELD node, score "
        "RETURN node.doc_id AS doc_id, "
        "node.page_content AS page_content, "
        "properties(node) AS metadata, "
        "score AS score "
        "ORDER BY score DESC"
    )


def maintenance_subgraph_query() -> str:
    return """
MATCH (wo:WorkOrder)-[:HAS_FAILURE]->(failure:Failure)
MATCH (wo)-[:FOR_ASSET]->(asset:Asset)-[:HAS_CLASS]->(asset_class:AssetClass)
OPTIONAL MATCH (wo)-[:CANDIDATE_PART]->(part:Part)
OPTIONAL MATCH (part)-[:STOCKED_AT]->(warehouse:Warehouse)
OPTIONAL MATCH (supplier:Supplier)-[:SUPPLIES]->(part)
WHERE
  ($failure_codes = [] OR failure.failure_code IN $failure_codes)
  AND ($asset_classes = [] OR asset_class.asset_class IN $asset_classes)
  AND ($work_order_ids = [] OR wo.work_order_id IN $work_order_ids)
  AND ($asset_ids = [] OR asset.asset_id IN $asset_ids)
  AND (
    $part_ids = []
    OR size($failure_codes) > 0
    OR size($asset_classes) > 0
    OR size($work_order_ids) > 0
    OR size($asset_ids) > 0
    OR part.part_id IN $part_ids
  )
RETURN
  wo.work_order_id AS work_order_id,
  asset.asset_id AS asset_id,
  asset.name AS asset_name,
  asset_class.asset_class AS asset_class,
  failure.failure_code AS failure_code,
  failure.failure_name AS failure_name,
  failure.root_cause AS root_cause,
  failure.recommended_action AS recommended_action,
  part.part_id AS part_id,
  part.part_name AS part_name,
  part.category AS part_category,
  part.criticality AS part_criticality,
  warehouse.warehouse AS warehouse,
  warehouse.stock_on_hand AS stock_on_hand,
  warehouse.min_stock AS min_stock,
  warehouse.reorder_point AS reorder_point,
  supplier.supplier_name AS supplier_name,
  supplier.reliability_score AS supplier_reliability_score
ORDER BY work_order_id, part_id, supplier_name
""".strip()


def sanitize_properties(properties: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in properties.items():
        if value is None:
            continue
        sanitized[safe_property(key)] = value
    return sanitized


def safe_label(value: str) -> str:
    if value not in NODE_TYPES and value not in {DOCUMENT_LABEL, DOMAIN_NODE_LABEL}:
        raise ValueError(f"Label nao permitida: {value}")
    return value


def safe_relationship(value: str) -> str:
    allowed = set(RELATIONSHIP_TYPES) | {"DESCRIBES", "MENTIONS", "MENTIONS_CLASS", "MENTIONS_PART"}
    if value not in allowed:
        raise ValueError(f"Relacionamento nao permitido: {value}")
    return value


def safe_identifier(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Identificador Neo4j invalido: {value}")
    return value


def safe_property(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"Propriedade Neo4j invalida: {value}")
    return value
