"""CLI de ingestao: CSV -> grafo -> documentos -> Chroma."""

from __future__ import annotations

import argparse
import sys

from method_01.graph_builder import DataValidationError, build_graph, write_artifacts
from method_01.settings import (
    CHROMA_DIR,
    DOCUMENTS_PATH,
    EDGES_PATH,
    NODES_PATH,
    configure_langsmith,
    require_openai_api_key,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingere CSVs brutos e constroi o indice GraphRAG local."
    )
    parser.add_argument(
        "--skip-vector-store",
        action="store_true",
        help="Gera JSONL do grafo/documentos sem chamar OpenAI ou Chroma.",
    )
    args = parser.parse_args(argv)

    configure_langsmith("method_01.script_ingestion")

    try:
        if not args.skip_vector_store:
            require_openai_api_key()

        result = build_graph()
        write_artifacts(result)

        print("Artefatos gerados:")
        print(f"- Nos: {len(result.nodes)} em {NODES_PATH}")
        print(f"- Arestas: {len(result.edges)} em {EDGES_PATH}")
        print(f"- Documentos: {len(result.documents)} em {DOCUMENTS_PATH}")
        print(f"- Tipos de nos: {dict(result.node_counts())}")
        print(f"- Tipos de arestas: {dict(result.edge_counts())}")

        if args.skip_vector_store:
            print("Chroma nao foi populado por causa de --skip-vector-store.")
            return 0

        from method_01.vector_store import build_vector_store

        indexed_count = build_vector_store(result.documents)
        print(f"Chroma populado com {indexed_count} documentos em {CHROMA_DIR}")
        return 0
    except (DataValidationError, RuntimeError, FileNotFoundError) as exc:
        print(f"Erro na ingestao: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
