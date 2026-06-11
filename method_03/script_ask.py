"""CLI de perguntas do Metodo 03: Text2Cypher validado + Neo4j + LLM."""

from __future__ import annotations

import argparse
import sys

from method_03.retrieval import ask_question, format_rows, validation_to_dict
from method_03.settings import (
    configure_method_03_environment,
    get_neo4j_read_settings,
    require_method_03_llm_runtime,
)
from method_03.validator import CypherValidationError, format_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pergunta ao Metodo 03 com Text2Cypher.")
    parser.add_argument("question", help="Pergunta em linguagem natural.")
    parser.add_argument("--max-rows", type=int, default=50, help="Limite maximo de linhas retornadas.")
    parser.add_argument("--show-cypher", action="store_true", help="Mostra Cypher gerado e validado.")
    parser.add_argument("--show-context", action="store_true", help="Mostra resultados retornados pelo Neo4j.")
    parser.add_argument("--dry-run", action="store_true", help="Gera e valida Cypher, mas nao executa.")
    args = parser.parse_args(argv)

    configure_method_03_environment("method_03.script_ask")

    try:
        require_method_03_llm_runtime()
        settings = None if args.dry_run else get_neo4j_read_settings()
        result = ask_question(
            args.question,
            max_rows=args.max_rows,
            dry_run=args.dry_run,
            settings=settings,
        )

        if args.show_cypher or args.dry_run:
            print("Cypher gerado e validado:")
            print(result["cypher"])
            print()
            print("Parametros:")
            print(format_rows([result["parameters"]]))
            print()
            print(format_validation(result["validation"]))
            if result["reasoning_summary"]:
                print()
                print(f"Resumo Text2Cypher: {result['reasoning_summary']}")

        if args.dry_run:
            return 0

        print(result["answer"])
        if args.show_context:
            print()
            print("Contexto Neo4j:")
            print(format_rows(result["rows"]))
        return 0
    except CypherValidationError as exc:
        print("Cypher gerado foi bloqueado pelo validador:", file=sys.stderr)
        print(format_validation(exc.result), file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Erro ao perguntar no Metodo 03: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
