"""Shared helpers for the Streamlit Method 01 app."""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from method_01.graph_builder import load_jsonl
from method_01.settings import (
    CHROMA_DIR,
    DOCUMENTS_PATH,
    EDGES_PATH,
    NODES_PATH,
    PROCESSED_DIR,
    RAW_DATA_DIR,
    configure_langsmith,
    get_chat_model_name,
    get_embedding_model_name,
)


APP_TITLE = "Method 01 - GraphRAG CSV"


def configure_app_environment(script_name: str) -> dict[str, str | None]:
    return configure_langsmith(script_name)


def artifact_status() -> dict[str, Any]:
    raw_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    return {
        "raw_csv_count": len(raw_files),
        "raw_files": raw_files,
        "processed_dir": PROCESSED_DIR,
        "nodes_exists": NODES_PATH.exists(),
        "edges_exists": EDGES_PATH.exists(),
        "documents_exists": DOCUMENTS_PATH.exists(),
        "chroma_exists": CHROMA_DIR.exists(),
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "chat_model": get_chat_model_name(),
        "embedding_model": get_embedding_model_name(),
    }


def load_nodes() -> list[dict[str, Any]]:
    return load_jsonl(NODES_PATH) if NODES_PATH.exists() else []


def load_edges() -> list[dict[str, Any]]:
    return load_jsonl(EDGES_PATH) if EDGES_PATH.exists() else []


def load_documents() -> list[dict[str, Any]]:
    return load_jsonl(DOCUMENTS_PATH) if DOCUMENTS_PATH.exists() else []


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame([flatten_record(record) for record in records])


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                flat[f"{key}.{child_key}"] = normalize_cell(child_value)
        else:
            flat[key] = normalize_cell(value)
    return flat


def normalize_cell(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return json.dumps(value, ensure_ascii=False)


def count_by(records: list[dict[str, Any]], field: str) -> pd.DataFrame:
    counter = Counter(record.get(field, "missing") for record in records)
    return pd.DataFrame(
        [{"name": key, "count": value} for key, value in sorted(counter.items())]
    )


def filter_by_text(
    records: list[dict[str, Any]], query: str, fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    if not query.strip():
        return records
    query_lower = query.lower()
    filtered = []
    for record in records:
        haystack = " ".join(str(resolve_path(record, field)) for field in fields)
        if query_lower in haystack.lower():
            filtered.append(record)
    return filtered


def resolve_path(record: dict[str, Any], dotted_path: str) -> Any:
    value: Any = record
    for part in dotted_path.split("."):
        if not isinstance(value, dict):
            return ""
        value = value.get(part, "")
    return value


def graph_to_dot(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    max_edges: int = 80,
) -> str:
    node_ids = {node["id"] for node in nodes}
    selected_edges = [
        edge
        for edge in edges
        if edge.get("source") in node_ids and edge.get("target") in node_ids
    ][:max_edges]
    selected_node_ids = {
        endpoint
        for edge in selected_edges
        for endpoint in (edge.get("source"), edge.get("target"))
    }
    if selected_node_ids:
        selected_nodes = [node for node in nodes if node.get("id") in selected_node_ids]
    else:
        selected_nodes = nodes[:max_edges]

    lines = [
        "digraph G {",
        '  graph [rankdir="LR", bgcolor="transparent", pad="0.2", nodesep="0.45", ranksep="0.75"];',
        '  node [shape=box, style="rounded,filled", color="#334155", fillcolor="#f8fafc", fontname="Arial", fontsize=10];',
        '  edge [color="#64748b", fontname="Arial", fontsize=9];',
    ]
    for node in selected_nodes:
        node_id = dot_id(node["id"])
        label = f"{node.get('type')}\\n{node.get('key')}"
        fill = node_color(node.get("type", ""))
        lines.append(f'  {node_id} [label="{escape_dot(label)}", fillcolor="{fill}"];')
    for edge in selected_edges:
        source = dot_id(edge["source"])
        target = dot_id(edge["target"])
        color = "#ea580c" if edge.get("provenance") == "inferred" else "#2563eb"
        label = escape_dot(edge.get("type", ""))
        lines.append(f'  {source} -> {target} [label="{label}", color="{color}"];')
    lines.append("}")
    return "\n".join(lines)


def node_color(node_type: str) -> str:
    colors = {
        "WorkOrder": "#eff6ff",
        "Asset": "#f0fdf4",
        "AssetClass": "#faf5ff",
        "Failure": "#fef2f2",
        "Part": "#fff7ed",
        "Supplier": "#f8fafc",
        "Warehouse": "#fefce8",
    }
    return colors.get(node_type, "#f8fafc")


def dot_id(value: str) -> str:
    return "n_" + re.sub(r"[^a-zA-Z0-9_]", "_", value)


def escape_dot(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def chroma_summary() -> str:
    if not CHROMA_DIR.exists():
        return "Nao criado"
    files = [path for path in CHROMA_DIR.rglob("*") if path.is_file()]
    return f"Criado ({len(files)} arquivos)"
