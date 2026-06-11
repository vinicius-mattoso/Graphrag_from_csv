"""CLI de inspecao do Metodo 03 no Neo4j."""

from __future__ import annotations

import argparse
import sys

from method_03.neo4j_store import get_driver, inspect_counts
from method_03.settings import configure_method_03_environment, get_neo4j_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspeciona dados do Metodo 03 no Neo4j.")
    parser.parse_args(argv)

    configure_method_03_environment("method_03.script_inspection")

    try:
        settings = get_neo4j_settings()
        driver = get_driver(settings)
        try:
            with driver.session(database=settings.database) as session:
                counts = inspect_counts(session)
        finally:
            driver.close()

        print("Resumo Neo4j Method 03")
        print(f"- Neo4j: {settings.uri} database={settings.database}")
        print("- Nos:")
        for row in counts["node_counts"]:
            print(f"  - {row['labels']}: {row['count']}")
        print("- Relacionamentos:")
        for row in counts["relationship_counts"]:
            print(f"  - {row['type']}: {row['count']}")
        return 0
    except RuntimeError as exc:
        print(f"Erro na inspecao Neo4j: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
