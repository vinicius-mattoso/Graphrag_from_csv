"""CLI de inspecao dos artefatos locais do grafo."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from method_01.graph_builder import load_jsonl
from method_01.settings import (
    CHROMA_DIR,
    DOCUMENTS_PATH,
    EDGES_PATH,
    NODES_PATH,
    configure_langsmith,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspeciona nos, arestas e documentos gerados pelo method_01."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Quantidade de exemplos por artefato.",
    )
    args = parser.parse_args(argv)

    configure_langsmith("method_01.script_inspection")

    try:
        _assert_artifacts_exist()
        nodes = load_jsonl(NODES_PATH)
        edges = load_jsonl(EDGES_PATH)
        documents = load_jsonl(DOCUMENTS_PATH)

        print("Resumo do Method 01")
        print(f"- Nos: {len(nodes)}")
        print(f"- Arestas: {len(edges)}")
        print(f"- Documentos: {len(documents)}")
        print(f"- Chroma: {_chroma_status()}")
        print()
        print("Nos por tipo:")
        _print_counter(Counter(node["type"] for node in nodes))
        print()
        print("Arestas por tipo:")
        _print_counter(Counter(edge["type"] for edge in edges))
        print()
        print("Arestas por proveniencia:")
        _print_counter(Counter(edge["provenance"] for edge in edges))
        print()
        _print_samples("Amostras de nos", nodes, args.samples)
        _print_samples("Amostras de arestas", edges, args.samples)
        _print_samples("Amostras de documentos", documents, args.samples)
        return 0
    except RuntimeError as exc:
        print(f"Erro na inspecao: {exc}", file=sys.stderr)
        return 1


def _assert_artifacts_exist() -> None:
    missing = [
        path
        for path in (NODES_PATH, EDGES_PATH, DOCUMENTS_PATH)
        if not path.exists()
    ]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise RuntimeError(
            f"Artefatos nao encontrados: {missing_text}. Execute primeiro "
            "python -m method_01.script_ingestion --skip-vector-store ou a "
            "ingestao completa."
        )


def _chroma_status() -> str:
    if not CHROMA_DIR.exists():
        return f"nao encontrado em {CHROMA_DIR}"
    return f"diretorio encontrado em {CHROMA_DIR}"


def _print_counter(counter: Counter) -> None:
    for key, value in sorted(counter.items()):
        print(f"- {key}: {value}")


def _print_samples(title: str, records: list[dict[str, Any]], samples: int) -> None:
    print(title + ":")
    for record in records[:samples]:
        print(f"- {_compact_record(record)}")
    print()


def _compact_record(record: dict[str, Any]) -> str:
    if "page_content" in record:
        metadata = record.get("metadata", {})
        content = record["page_content"]
        return (
            f"{record.get('id')} metadata={metadata} "
            f"content={content[:140]}"
        )
    if "source" in record and "target" in record:
        return (
            f"{record['id']} provenance={record['provenance']} "
            f"properties={record.get('properties', {})}"
        )
    return f"{record.get('id')} properties={record.get('properties', {})}"


if __name__ == "__main__":
    raise SystemExit(main())
