"""Recuperacao GraphRAG no Neo4j usando vector index + Cypher controlado."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
import unicodedata

from method_01.settings import get_chat_model_name
from method_02.cypher import maintenance_subgraph_query, vector_search_query
from method_02.neo4j_store import get_driver
from method_02.settings import Neo4jSettings, get_neo4j_settings


def retrieve_subgraph(question: str, k: int = 8, settings: Neo4jSettings | None = None) -> dict[str, Any]:
    settings = settings or get_neo4j_settings()
    query_embedding = embed_query(question, settings)
    hints = infer_structured_hints(question)

    driver = get_driver(settings)
    try:
        with driver.session(database=settings.database) as session:
            vector_rows = session.run(
                vector_search_query(settings),
                k=k,
                embedding=query_embedding,
            ).data()
            seeds = merge_vector_seeds_with_hints(vector_rows, hints)
            subgraph_rows = session.run(maintenance_subgraph_query(), **seeds).data()
    finally:
        driver.close()

    return {
        "question": question,
        "vector_results": clean_vector_rows(vector_rows),
        "seeds": seeds,
        "subgraph": subgraph_rows,
    }


def answer_question(question: str, k: int = 8, settings: Neo4jSettings | None = None) -> dict[str, Any]:
    retrieval = retrieve_subgraph(question, k=k, settings=settings)
    context = format_retrieval_context(retrieval)
    answer = generate_answer(question, context)
    return {"answer": answer, **retrieval, "context": context}


def embed_query(question: str, settings: Neo4jSettings) -> list[float]:
    try:
        from langchain_openai import OpenAIEmbeddings
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependencia ausente: instale langchain-openai.") from exc

    embeddings = OpenAIEmbeddings(model=settings.embedding_model)
    return embeddings.embed_query(question)


def generate_answer(question: str, context: str) -> str:
    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependencias LangChain ausentes para gerar resposta.") from exc

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Voce responde perguntas sobre manutencao industrial usando apenas "
                "o contexto recuperado do Neo4j. Se faltar informacao, diga isso. "
                "Responda em portugues e cite IDs relevantes.",
            ),
            (
                "human",
                "Pergunta: {question}\n\nContexto recuperado do Neo4j:\n{context}",
            ),
        ]
    )
    chain = prompt | ChatOpenAI(model=get_chat_model_name(), temperature=0) | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


def infer_structured_hints(question: str) -> dict[str, list[str]]:
    normalized = normalize_text(question)
    hints = {
        "failure_codes": [],
        "asset_classes": [],
        "work_order_ids": [],
        "asset_ids": [],
        "part_ids": [],
    }

    if "queda" in normalized and "pressao" in normalized:
        hints["failure_codes"].append("F-QUEDA_PRESSAO")
    if "vibracao" in normalized:
        hints["failure_codes"].append("F-VIBRACAO")
    if "superaquec" in normalized or "temperatura" in normalized:
        hints["failure_codes"].append("F-SUPERAQUECIMENTO")
    if "ruido" in normalized and "rolamento" in normalized:
        hints["failure_codes"].append("F-RUIDO_ROLAMENTO")
    if "troca termica" in normalized or "termica" in normalized:
        hints["failure_codes"].append("F-TROCA_TERMICA_BAIXA")

    if "compressor" in normalized:
        hints["asset_classes"].append("COMPRESSOR_AR")
    if "bomba" in normalized:
        hints["asset_classes"].append("BOMBA_CENTRIFUGA")
    if "transportador" in normalized or "correia" in normalized:
        hints["asset_classes"].append("TRANSPORTADOR_CORREIA")
    if "trocador" in normalized or "calor" in normalized:
        hints["asset_classes"].append("TROCADOR_CALOR")

    return {key: sorted(set(value)) for key, value in hints.items()}


def merge_vector_seeds_with_hints(
    vector_rows: list[dict[str, Any]],
    hints: dict[str, list[str]],
) -> dict[str, list[str]]:
    seeds = defaultdict(set)
    for key, values in hints.items():
        seeds[key].update(values)

    for row in vector_rows:
        metadata = row.get("metadata", {})
        _add_if_present(seeds, "failure_codes", metadata.get("failure_code"))
        _add_if_present(seeds, "asset_classes", metadata.get("asset_class"))
        _add_if_present(seeds, "work_order_ids", metadata.get("work_order_id"))
        _add_if_present(seeds, "asset_ids", metadata.get("asset_id"))
        _add_if_present(seeds, "part_ids", metadata.get("part_id"))

    if hints.get("asset_classes"):
        seeds["asset_classes"] = set(hints["asset_classes"])
    if hints.get("failure_codes"):
        seeds["failure_codes"] = set(hints["failure_codes"])
    if hints.get("asset_classes") or hints.get("failure_codes"):
        seeds["work_order_ids"] = set()
        seeds["asset_ids"] = set()
        seeds["part_ids"] = set()

    return {
        "failure_codes": sorted(seeds["failure_codes"]),
        "asset_classes": sorted(seeds["asset_classes"]),
        "work_order_ids": sorted(seeds["work_order_ids"]),
        "asset_ids": sorted(seeds["asset_ids"]),
        "part_ids": sorted(seeds["part_ids"]),
    }


def format_retrieval_context(retrieval: dict[str, Any]) -> str:
    lines = ["Vector results:"]
    for row in retrieval["vector_results"]:
        lines.append(
            f"- {row.get('doc_id')} score={row.get('score'):.4f} "
            f"type={row.get('metadata', {}).get('doc_type')} "
            f"text={row.get('page_content')}"
        )

    lines.append("\nSubgraph rows:")
    for row in retrieval["subgraph"]:
        lines.append(
            "- "
            + ", ".join(
                f"{key}={value}"
                for key, value in row.items()
                if value is not None
            )
        )
    return "\n".join(lines)


def clean_vector_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for row in rows:
        metadata = dict(row.get("metadata") or {})
        metadata.pop("embedding", None)
        cleaned.append({**row, "metadata": metadata})
    return cleaned


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _add_if_present(seeds: dict[str, set[str]], key: str, value: Any) -> None:
    if value:
        seeds[key].add(str(value))
