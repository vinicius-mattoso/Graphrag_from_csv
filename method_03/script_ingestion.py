"""CLI de ingestao do Metodo 03: CSV -> Neo4j."""

from __future__ import annotations

import argparse
import sys

from method_01.graph_builder import DataValidationError
from method_03.neo4j_store import ingest_graph_to_neo4j, prepare_graph_payload
from method_03.settings import configure_method_03_environment, get_neo4j_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingere CSVs no Neo4j para o Metodo 03.")
    parser.add_argument("--reset", action="store_true", help="Remove dados method_03 antes de ingerir.")
    args = parser.parse_args(argv)

    configure_method_03_environment("method_03.script_ingestion")

    try:
        settings = get_neo4j_settings()
        result = prepare_graph_payload()
        stats = ingest_graph_to_neo4j(result, settings=settings, reset=args.reset)
        print("Metodo 03 ingerido no Neo4j:")
        print(f"- Nos: {stats['nodes']}")
        print(f"- Arestas: {stats['edges']}")
        print(f"- Neo4j: {settings.uri} database={settings.database}")
        return 0
    except (RuntimeError, DataValidationError, FileNotFoundError) as exc:
        print(f"Erro na ingestao Neo4j: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
