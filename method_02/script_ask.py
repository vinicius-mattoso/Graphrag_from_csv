"""CLI de perguntas do Metodo 02: Neo4j vector index + Cypher + LLM."""

from __future__ import annotations

import argparse
import json
import sys

from method_01.settings import require_openai_api_key
from method_02.retrieval import answer_question, retrieve_subgraph
from method_02.settings import configure_method_02_environment, get_neo4j_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pergunta ao GraphRAG Neo4j do Metodo 02.")
    parser.add_argument("question", help="Pergunta em linguagem natural.")
    parser.add_argument("--k", type=int, default=8, help="Top-k do vector index Neo4j.")
    parser.add_argument("--show-context", action="store_true", help="Mostra vector results e subgrafo.")
    parser.add_argument("--no-llm", action="store_true", help="Recupera subgrafo sem gerar resposta final.")
    args = parser.parse_args(argv)

    configure_method_02_environment("method_02.script_ask")

    try:
        require_openai_api_key()
        settings = get_neo4j_settings()
        if args.no_llm:
            retrieval = retrieve_subgraph(args.question, k=args.k, settings=settings)
            print(json.dumps(retrieval, ensure_ascii=False, indent=2))
            return 0

        result = answer_question(args.question, k=args.k, settings=settings)
        print(result["answer"])
        if args.show_context:
            print("\nContexto Neo4j:")
            print(result["context"])
        return 0
    except RuntimeError as exc:
        print(f"Erro ao perguntar no Neo4j: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
