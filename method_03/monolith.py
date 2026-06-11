"""Versao didatica e linear do Metodo 03.

Este arquivo junta o processo inteiro em um unico entrypoint para facilitar a
leitura: CSV -> grafo -> Neo4j -> Text2Cypher -> validacao -> execucao -> LLM.
Os modulos do pacote continuam sendo a versao recomendada para manutencao.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from method_01.graph_builder import DataValidationError, build_graph
from method_03.neo4j_store import ingest_graph_to_neo4j, run_read_query
from method_03.retrieval import format_rows, generate_answer
from method_03.schema import allowed_labels, allowed_relationships, build_examples_text
from method_03.settings import (
    configure_method_03_environment,
    get_method_03_chat_model_name,
    get_neo4j_settings,
    get_neo4j_read_settings,
    require_method_03_llm_runtime,
)
from method_03.text2cypher import generate_cypher
from method_03.validator import CypherValidationError, format_validation, require_valid_cypher


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monolito didatico do Metodo 03.")
    parser.add_argument("question", help="Pergunta em linguagem natural.")
    parser.add_argument("--reset", action="store_true", help="Remove dados method_03 antes da ingestao.")
    parser.add_argument("--max-rows", type=int, default=50, help="Limite maximo de linhas retornadas.")
    parser.add_argument(
        "--engine",
        choices=("langchain", "custom"),
        default="langchain",
        help="Motor Text2Cypher: langchain usa GraphCypherQAChain; custom usa os modulos locais.",
    )
    args = parser.parse_args(argv)

    configure_method_03_environment("method_03.monolith")

    try:
        print("1. Validando ambiente")
        require_method_03_llm_runtime()
        settings = get_neo4j_settings()
        print(f"   Neo4j: {settings.uri} database={settings.database}")

        print("2. Lendo CSVs e construindo grafo em memoria")
        graph = build_graph()
        print(f"   Nos: {len(graph.nodes)} | Arestas: {len(graph.edges)}")

        print("3. Gravando grafo no Neo4j")
        stats = ingest_graph_to_neo4j(graph, settings=settings, reset=args.reset)
        print(f"   Gravado: {stats['nodes']} nos, {stats['edges']} arestas")

        if args.engine == "langchain":
            _run_langchain_graph_cypher_chain(args.question, max_rows=args.max_rows)
        else:
            _run_custom_text2cypher(args.question, max_rows=args.max_rows, settings=settings)
        return 0
    except CypherValidationError as exc:
        print("Cypher bloqueado pelo validador:", file=sys.stderr)
        print(format_validation(exc.result), file=sys.stderr)
        return 1
    except (RuntimeError, DataValidationError, FileNotFoundError) as exc:
        print(f"Erro no monolito do Metodo 03: {exc}", file=sys.stderr)
        return 1


def _run_custom_text2cypher(question: str, *, max_rows: int, settings) -> None:
    print("4. Gerando Cypher com LLM pelos modulos locais")
    generation = generate_cypher(question, max_rows=max_rows)
    print(generation.cypher)
    if generation.parameters:
        print(f"   Parametros: {generation.parameters}")

    print("5. Validando Cypher")
    validation = require_valid_cypher(generation.cypher, max_rows=max_rows)
    print(format_validation(validation))

    print("6. Executando Cypher validado no Neo4j")
    rows = run_read_query(validation.cypher, generation.parameters, settings=settings)
    print(format_rows(rows))

    print("7. Gerando resposta final com LLM")
    answer = generate_answer(
        question=question,
        cypher=validation.cypher,
        parameters=generation.parameters,
        rows=rows,
        reasoning_summary=generation.reasoning_summary,
    )
    print(answer)


def _run_langchain_graph_cypher_chain(question: str, *, max_rows: int) -> None:
    print("4. Executando Text2Cypher com langchain_neo4j.GraphCypherQAChain")
    try:
        from langchain_core.prompts import PromptTemplate
        from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
        from langchain_openai import ChatOpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencias ausentes: instale langchain-neo4j, langchain-core "
            "e langchain-openai para usar --engine langchain."
        ) from exc

    read_settings = get_neo4j_read_settings()

    class ValidatedNeo4jGraph(Neo4jGraph):
        def query(
            self,
            query: str,
            params: dict[str, Any] = {},
            session_params: dict[str, Any] = {},
        ) -> list[dict[str, Any]]:
            print("5. Validando Cypher gerado pelo LangChain")
            validation = require_valid_cypher(query, max_rows=max_rows)
            print(validation.cypher)
            print(format_validation(validation))
            print("6. Executando Cypher validado no Neo4j")
            return super().query(
                validation.cypher,
                params=params,
                session_params=session_params,
            )

    graph = ValidatedNeo4jGraph(
        url=read_settings.uri,
        username=read_settings.username,
        password=read_settings.password,
        database=read_settings.database,
    )
    llm = ChatOpenAI(model=get_method_03_chat_model_name(), temperature=0)
    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question", "examples"],
        template=_langchain_cypher_prompt(max_rows),
    )
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        cypher_prompt=cypher_prompt,
        include_types=sorted(allowed_labels() | allowed_relationships()),
        validate_cypher=True,
        return_intermediate_steps=True,
        allow_dangerous_requests=True,
        top_k=max_rows,
    )

    result = chain.invoke(
        {
            "query": question,
            "examples": build_examples_text(),
        }
    )
    print("7. Resposta final do GraphCypherQAChain")
    print(result["result"])
    if result.get("intermediate_steps"):
        print()
        print("Passos intermediarios LangChain:")
        print(format_rows(result["intermediate_steps"]))


def _langchain_cypher_prompt(max_rows: int) -> str:
    return f"""Task: Generate one read-only Cypher statement to query a Neo4j graph database.
Instructions:
- Use only the provided relationship types and properties in the schema.
- Do not use any relationship type, label, or property that is not provided.
- Use only MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT, and SKIP.
- Never use CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, LOAD CSV, CALL, APOC, FOREACH, or USE.
- Always include LIMIT less than or equal to {max_rows}.
- For inventory, stock_on_hand, min_stock, and reorder_point are properties on the STOCKED_AT relationship.
- Do not include explanations, apologies, markdown, or text outside the Cypher statement.

Schema:
{{schema}}

Examples:
{{examples}}

Question:
{{question}}"""


if __name__ == "__main__":
    raise SystemExit(main())
