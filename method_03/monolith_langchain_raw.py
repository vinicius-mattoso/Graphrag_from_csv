"""Monolito LangChain puro para estudar GraphCypherQAChain.

Este script evita os guardrails locais do Metodo 03 de proposito: nao usa
ValidatedNeo4jGraph, nao chama validator.py, nao filtra schema por ontologia e
nao usa prompt customizado do projeto. A ideia e observar o comportamento nativo
do framework LangChain/Neo4j.
"""

from __future__ import annotations

import argparse
import sys

from method_01.graph_builder import DataValidationError, build_graph
from method_03.neo4j_store import ingest_graph_to_neo4j
from method_03.retrieval import format_rows
from method_03.settings import (
    configure_method_03_environment,
    get_method_03_chat_model_name,
    get_neo4j_read_settings,
    get_neo4j_settings,
    require_method_03_llm_runtime,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Monolito LangChain puro: GraphCypherQAChain sem guardrails locais."
    )
    parser.add_argument("question", help="Pergunta em linguagem natural.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove dados method_03 antes da ingestao.",
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Nao ingere CSVs; usa o grafo ja existente no Neo4j.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Quantidade de linhas que a chain usa como contexto.",
    )
    parser.add_argument(
        "--no-validate-cypher",
        action="store_true",
        help="Desliga tambem o corretor Cypher nativo do LangChain.",
    )
    args = parser.parse_args(argv)

    configure_method_03_environment("method_03.monolith_langchain_raw")

    try:
        print("1. Validando ambiente")
        require_method_03_llm_runtime()
        write_settings = get_neo4j_settings()
        read_settings = get_neo4j_read_settings()
        print(f"   Neo4j escrita: {write_settings.uri} database={write_settings.database}")
        print(f"   Neo4j consulta: usuario={read_settings.username}")

        if not args.skip_ingestion:
            print("2. Lendo CSVs e gravando grafo no Neo4j")
            graph = build_graph()
            stats = ingest_graph_to_neo4j(graph, settings=write_settings, reset=args.reset)
            print(f"   Gravado: {stats['nodes']} nos, {stats['edges']} arestas")
        else:
            print("2. Ingestao ignorada por --skip-ingestion")

        print("3. Criando Neo4jGraph puro do LangChain")
        graph_store = _build_langchain_graph(read_settings)
        print("   Schema descoberto pelo LangChain:")
        print(graph_store.schema)

        print("4. Criando GraphCypherQAChain puro")
        chain = _build_graph_cypher_chain(
            graph_store=graph_store,
            top_k=args.top_k,
            validate_cypher=not args.no_validate_cypher,
        )

        print("5. Executando pergunta sem validador local")
        result = chain.invoke({"query": args.question})

        print("Resposta:")
        print(result["result"])
        if result.get("intermediate_steps"):
            print()
            print("Passos intermediarios LangChain:")
            print(format_rows(result["intermediate_steps"]))
        return 0
    except (RuntimeError, DataValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Erro no monolito LangChain puro: {exc}", file=sys.stderr)
        return 1


def _build_langchain_graph(settings):
    try:
        from langchain_neo4j import Neo4jGraph
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependencia ausente: instale langchain-neo4j.") from exc

    return Neo4jGraph(
        url=settings.uri,
        username=settings.username,
        password=settings.password,
        database=settings.database,
        refresh_schema=True,
    )


def _build_graph_cypher_chain(*, graph_store, top_k: int, validate_cypher: bool):
    try:
        from langchain_neo4j import GraphCypherQAChain
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencias ausentes: instale langchain-neo4j e langchain-openai."
        ) from exc

    llm = ChatOpenAI(model=get_method_03_chat_model_name(), temperature=0)
    return GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph_store,
        validate_cypher=validate_cypher,
        return_intermediate_steps=True,
        allow_dangerous_requests=True,
        top_k=top_k,
    )


if __name__ == "__main__":
    raise SystemExit(main())
