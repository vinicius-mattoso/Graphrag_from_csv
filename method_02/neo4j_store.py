"""Persistencia do grafo e documentos no Neo4j."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Iterable

from method_01.graph_builder import GraphBuildResult, build_graph
from method_02.cypher import (
    METHOD_SOURCE,
    constraint_queries,
    index_queries,
    reset_query,
    sanitize_properties,
    upsert_document_link_query,
    upsert_document_query,
    upsert_edge_query,
    upsert_node_query,
)
from method_02.settings import Neo4jSettings, get_neo4j_settings


def get_driver(settings: Neo4jSettings | None = None):
    try:
        from neo4j import GraphDatabase
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale neo4j/langchain-neo4j antes de usar o Metodo 02."
        ) from exc

    settings = settings or get_neo4j_settings()
    return GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password))


def prepare_graph_payload() -> GraphBuildResult:
    return build_graph()


def create_schema(session, settings: Neo4jSettings) -> None:
    for query in constraint_queries():
        session.run(query)
    for query in index_queries(settings):
        session.run(query)


def reset_method_02_data(session) -> None:
    session.run(reset_query(), source_system=METHOD_SOURCE)


def ingest_graph_to_neo4j(
    result: GraphBuildResult,
    *,
    settings: Neo4jSettings,
    reset: bool = False,
    skip_embeddings: bool = False,
) -> dict[str, int]:
    driver = get_driver(settings)
    try:
        with driver.session(database=settings.database) as session:
            create_schema(session, settings)
            if reset:
                reset_method_02_data(session)

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

            document_count = 0
            if not skip_embeddings:
                embeddings = embed_documents([doc["page_content"] for doc in result.documents])
            else:
                embeddings = [[] for _ in result.documents]

            for document, embedding in zip(result.documents, embeddings):
                session.run(
                    upsert_document_query(),
                    doc_id=document["id"],
                    page_content=document["page_content"],
                    embedding=embedding,
                    metadata=document_metadata_properties(document),
                    source_system=METHOD_SOURCE,
                )
                for link in document_links(document):
                    session.run(
                        upsert_document_link_query(link["relationship_type"]),
                        doc_id=document["id"],
                        node_id=link["node_id"],
                        source_system=METHOD_SOURCE,
                    )
                document_count += 1

            return {
                "nodes": len(result.nodes),
                "edges": len(result.edges),
                "documents": document_count,
            }
    finally:
        driver.close()


def embed_documents(texts: list[str]) -> list[list[float]]:
    try:
        from langchain_openai import OpenAIEmbeddings
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependencia ausente: instale langchain-openai.") from exc

    settings = get_neo4j_settings()
    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    return embeddings.embed_documents(texts)


def document_metadata_properties(document: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(document["metadata"])
    metadata["metadata_json"] = json.dumps(document["metadata"], ensure_ascii=False)
    metadata["graph_type"] = "GraphDocument"
    return sanitize_properties(metadata)


def document_links(document: dict[str, Any]) -> list[dict[str, str]]:
    metadata = document["metadata"]
    doc_type = metadata.get("doc_type")
    links: list[dict[str, str]] = []

    if doc_type == "AssetClass" and metadata.get("asset_class"):
        links.append(_link("DESCRIBES", f"AssetClass:{metadata['asset_class']}"))
    elif doc_type == "Asset" and metadata.get("asset_id"):
        links.append(_link("DESCRIBES", f"Asset:{metadata['asset_id']}"))
    elif doc_type == "Failure" and metadata.get("failure_code"):
        links.append(_link("DESCRIBES", f"Failure:{metadata['failure_code']}"))
    elif doc_type == "WorkOrder" and metadata.get("work_order_id"):
        links.append(_link("DESCRIBES", f"WorkOrder:{metadata['work_order_id']}"))
    elif doc_type == "Part" and metadata.get("part_id"):
        links.append(_link("DESCRIBES", f"Part:{metadata['part_id']}"))
        if metadata.get("asset_class"):
            links.append(_link("MENTIONS_CLASS", f"AssetClass:{metadata['asset_class']}"))
    elif doc_type == "Warehouse" and metadata.get("warehouse"):
        links.append(_link("DESCRIBES", f"Warehouse:{metadata['warehouse']}"))
        if metadata.get("part_id"):
            links.append(_link("MENTIONS_PART", f"Part:{metadata['part_id']}"))
    elif doc_type == "Supplier" and metadata.get("supplier_name"):
        links.append(_link("DESCRIBES", f"Supplier:{metadata['supplier_name']}"))
        if metadata.get("part_id"):
            links.append(_link("MENTIONS_PART", f"Part:{metadata['part_id']}"))

    return links


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
    document_count = session.run(
        """
        MATCH (d:GraphDocument)
        WHERE d.source_system = $source_system
        RETURN count(d) AS count
        """,
        source_system=METHOD_SOURCE,
    ).single()["count"]
    return {
        "node_counts": node_counts,
        "relationship_counts": relationship_counts,
        "document_count": document_count,
    }


def _link(relationship_type: str, node_id: str) -> dict[str, str]:
    return {"relationship_type": relationship_type, "node_id": node_id}
