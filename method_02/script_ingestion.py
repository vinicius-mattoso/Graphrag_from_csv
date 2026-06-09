"""CLI de ingestao do Metodo 02: CSV -> Neo4j + vector index."""

from __future__ import annotations

import argparse
import sys

from method_01.graph_builder import DataValidationError
from method_02.neo4j_store import ingest_graph_to_neo4j, prepare_graph_payload
from method_02.settings import configure_method_02_environment, get_neo4j_settings, require_method_02_runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingere CSVs no Neo4j para GraphRAG.")
    parser.add_argument("--reset", action="store_true", help="Remove dados method_02 antes de ingerir.")
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Carrega grafo e documentos sem embeddings/vector index populado.",
    )
    args = parser.parse_args(argv)

    configure_method_02_environment("method_02.script_ingestion")

    try:
        settings = get_neo4j_settings() if args.skip_embeddings else require_method_02_runtime()
        result = prepare_graph_payload()
        stats = ingest_graph_to_neo4j(
            result,
            settings=settings,
            reset=args.reset,
            skip_embeddings=args.skip_embeddings,
        )
        print("Metodo 02 ingerido no Neo4j:")
        print(f"- Nos: {stats['nodes']}")
        print(f"- Arestas: {stats['edges']}")
        print(f"- Documentos: {stats['documents']}")
        print(f"- Neo4j: {settings.uri} database={settings.database}")
        print(f"- Vector index: {settings.vector_index_name}")
        if args.skip_embeddings:
            print("- Embeddings: ignorados por --skip-embeddings")
        return 0
    except (RuntimeError, DataValidationError, FileNotFoundError) as exc:
        print(f"Erro na ingestao Neo4j: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
