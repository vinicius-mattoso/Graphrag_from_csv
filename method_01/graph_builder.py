"""Construcao deterministica do grafo a partir dos CSVs brutos."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from method_01.ontology import (
    CSV_REQUIRED_COLUMNS,
    NODE_TYPES,
    PRIMARY_KEYS,
    RELATIONSHIP_TYPES,
    assert_known_node_type,
    assert_known_relationship_type,
)
from method_01.settings import DOCUMENTS_PATH, EDGES_PATH, NODES_PATH, RAW_DATA_DIR


class DataValidationError(ValueError):
    """Raised when raw CSVs cannot be transformed into the ontology."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str
    key: str
    properties: dict[str, Any]


@dataclass(frozen=True)
class GraphEdge:
    id: str
    type: str
    source: str
    target: str
    provenance: str
    properties: dict[str, Any]


@dataclass(frozen=True)
class GraphBuildResult:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    documents: list[dict[str, Any]]

    def node_counts(self) -> Counter:
        return Counter(node.type for node in self.nodes)

    def edge_counts(self) -> Counter:
        return Counter(edge.type for edge in self.edges)


RawTables = dict[str, list[dict[str, str]]]


def read_csv_tables(raw_dir: Path = RAW_DATA_DIR) -> RawTables:
    tables: RawTables = {}
    for filename in CSV_REQUIRED_COLUMNS:
        path = raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"CSV obrigatorio nao encontrado: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            tables[filename] = list(csv.DictReader(handle))
    return tables


def validate_raw_tables(tables: RawTables) -> None:
    errors: list[str] = []

    for filename, required_columns in CSV_REQUIRED_COLUMNS.items():
        rows = tables.get(filename, [])
        observed_columns = set(rows[0].keys()) if rows else set()
        missing_columns = set(required_columns) - observed_columns
        if missing_columns:
            errors.append(
                f"{filename}: colunas ausentes: {', '.join(sorted(missing_columns))}"
            )

        primary_key = PRIMARY_KEYS[filename]
        values = [row.get(primary_key, "").strip() for row in rows]
        missing_values = [idx for idx, value in enumerate(values, start=2) if not value]
        if missing_values:
            errors.append(
                f"{filename}: chave {primary_key} vazia nas linhas {missing_values}"
            )
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            errors.append(
                f"{filename}: valores duplicados em {primary_key}: {duplicates}"
            )

    assets = tables.get("assets.csv", [])
    failures = tables.get("failures.csv", [])
    parts = tables.get("parts.csv", [])
    inventory = tables.get("inventory.csv", [])
    suppliers = tables.get("suppliers.csv", [])
    work_orders = tables.get("work_orders.csv", [])

    asset_ids = {row["asset_id"] for row in assets}
    failure_codes = {row["failure_code"] for row in failures}
    part_ids = {row["part_id"] for row in parts}
    asset_classes = {row["asset_class"] for row in assets}

    _append_orphans(
        errors,
        "work_orders.csv",
        "asset_id",
        (row["asset_id"] for row in work_orders),
        asset_ids,
    )
    _append_orphans(
        errors,
        "work_orders.csv",
        "failure_code",
        (row["failure_code"] for row in work_orders),
        failure_codes,
    )
    _append_orphans(
        errors,
        "inventory.csv",
        "part_id",
        (row["part_id"] for row in inventory),
        part_ids,
    )
    _append_orphans(
        errors,
        "suppliers.csv",
        "part_id",
        (row["part_id"] for row in suppliers),
        part_ids,
    )

    part_classes = {
        asset_class
        for row in parts
        for asset_class in parse_compatible_asset_classes(row["compatible_asset_class"])
    }
    unknown_classes = sorted(part_classes - asset_classes)
    if unknown_classes:
        errors.append(
            "parts.csv: compatible_asset_class sem AssetClass correspondente: "
            + ", ".join(unknown_classes)
        )

    for row in work_orders:
        opened_at = _parse_date(row["opened_at"], "opened_at", row["work_order_id"])
        closed_at_raw = row.get("closed_at", "").strip()
        if row.get("status") == "Fechada" and not closed_at_raw:
            errors.append(
                f"work_orders.csv: {row['work_order_id']} esta Fechada sem closed_at"
            )
        if closed_at_raw:
            closed_at = _parse_date(closed_at_raw, "closed_at", row["work_order_id"])
            if closed_at < opened_at:
                errors.append(
                    f"work_orders.csv: {row['work_order_id']} tem closed_at "
                    "anterior a opened_at"
                )

    if errors:
        raise DataValidationError(errors)


def build_graph(raw_dir: Path = RAW_DATA_DIR) -> GraphBuildResult:
    tables = read_csv_tables(raw_dir)
    validate_raw_tables(tables)

    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}

    assets = tables["assets.csv"]
    failures = tables["failures.csv"]
    parts = tables["parts.csv"]
    inventory = tables["inventory.csv"]
    suppliers = tables["suppliers.csv"]
    work_orders = tables["work_orders.csv"]

    assets_by_id = {row["asset_id"]: row for row in assets}
    failures_by_code = {row["failure_code"]: row for row in failures}
    parts_by_id = {row["part_id"]: row for row in parts}
    inventory_by_part = {row["part_id"]: row for row in inventory}
    suppliers_by_part: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in suppliers:
        suppliers_by_part[row["part_id"]].append(row)

    all_asset_classes = sorted(
        {row["asset_class"] for row in assets}
        | {
            asset_class
            for row in parts
            for asset_class in parse_compatible_asset_classes(
                row["compatible_asset_class"]
            )
        }
    )
    for asset_class in all_asset_classes:
        _add_node(
            nodes,
            "AssetClass",
            asset_class,
            {"asset_class": asset_class, "source_files": ["assets.csv", "parts.csv"]},
        )

    for row in assets:
        _add_node(nodes, "Asset", row["asset_id"], dict(row))
        _add_edge(
            edges,
            "HAS_CLASS",
            _node_id("Asset", row["asset_id"]),
            _node_id("AssetClass", row["asset_class"]),
            {
                "join_key": "asset_class",
                "source_file": "assets.csv",
                "asset_class": row["asset_class"],
            },
        )

    for row in failures:
        _add_node(nodes, "Failure", row["failure_code"], dict(row))

    for row in parts:
        _add_node(
            nodes,
            "Part",
            row["part_id"],
            {
                **row,
                "compatible_asset_classes": parse_compatible_asset_classes(
                    row["compatible_asset_class"]
                ),
                "lead_time_days": _to_int(row["lead_time_days"]),
                "unit_cost": _to_float(row["unit_cost"]),
            },
        )
        for asset_class in parse_compatible_asset_classes(row["compatible_asset_class"]):
            _add_edge(
                edges,
                "COMPATIBLE_WITH",
                _node_id("Part", row["part_id"]),
                _node_id("AssetClass", asset_class),
                {
                    "source_column": "compatible_asset_class",
                    "source_file": "parts.csv",
                    "asset_class": asset_class,
                },
                qualifier=asset_class,
            )

    for row in inventory:
        _add_node(nodes, "Warehouse", row["warehouse"], {"warehouse": row["warehouse"]})
        _add_edge(
            edges,
            "STOCKED_AT",
            _node_id("Part", row["part_id"]),
            _node_id("Warehouse", row["warehouse"]),
            {
                "warehouse": row["warehouse"],
                "stock_on_hand": _to_int(row["stock_on_hand"]),
                "min_stock": _to_int(row["min_stock"]),
                "reorder_point": _to_int(row["reorder_point"]),
                "last_counted_at": row["last_counted_at"],
                "source_file": "inventory.csv",
            },
        )

    supplier_ids_by_name: dict[str, list[str]] = defaultdict(list)
    for row in suppliers:
        supplier_ids_by_name[row["supplier_name"]].append(row["supplier_id"])
    for supplier_name, supplier_ids in supplier_ids_by_name.items():
        _add_node(
            nodes,
            "Supplier",
            supplier_name,
            {
                "supplier_name": supplier_name,
                "supplier_ids": sorted(supplier_ids),
            },
        )
    for row in suppliers:
        _add_edge(
            edges,
            "SUPPLIES",
            _node_id("Supplier", row["supplier_name"]),
            _node_id("Part", row["part_id"]),
            {
                "supplier_id": row["supplier_id"],
                "supplier_name": row["supplier_name"],
                "preferred": _to_bool(row["preferred"]),
                "average_delivery_days": _to_int(row["average_delivery_days"]),
                "reliability_score": _to_float(row["reliability_score"]),
                "source_file": "suppliers.csv",
            },
            qualifier=row["supplier_id"],
        )

    for row in work_orders:
        _add_node(
            nodes,
            "WorkOrder",
            row["work_order_id"],
            {
                **row,
                "downtime_hours": _to_float(row["downtime_hours"]),
            },
        )
        asset = assets_by_id[row["asset_id"]]
        _add_edge(
            edges,
            "FOR_ASSET",
            _node_id("WorkOrder", row["work_order_id"]),
            _node_id("Asset", row["asset_id"]),
            {
                "join_key": "asset_id",
                "source_file": "work_orders.csv",
                "asset_id": row["asset_id"],
            },
        )
        _add_edge(
            edges,
            "HAS_FAILURE",
            _node_id("WorkOrder", row["work_order_id"]),
            _node_id("Failure", row["failure_code"]),
            {
                "join_key": "failure_code",
                "source_file": "work_orders.csv",
                "failure_code": row["failure_code"],
            },
        )
        for part in _candidate_parts_for_asset_class(parts, asset["asset_class"]):
            _add_edge(
                edges,
                "CANDIDATE_PART",
                _node_id("WorkOrder", row["work_order_id"]),
                _node_id("Part", part["part_id"]),
                {
                    "asset_class": asset["asset_class"],
                    "inference_rule": "asset.asset_class in part.compatible_asset_class",
                    "source_work_order_id": row["work_order_id"],
                    "part_id": part["part_id"],
                    "confidence": 1.0,
                },
                qualifier=f"{row['work_order_id']}:{part['part_id']}",
            )

    documents = build_document_records(
        assets=assets,
        failures=failures,
        parts=parts,
        inventory_by_part=inventory_by_part,
        suppliers_by_part=suppliers_by_part,
        work_orders=work_orders,
        assets_by_id=assets_by_id,
        failures_by_code=failures_by_code,
        all_asset_classes=all_asset_classes,
    )

    return GraphBuildResult(
        nodes=sorted(nodes.values(), key=lambda node: (node.type, node.id)),
        edges=sorted(edges.values(), key=lambda edge: (edge.type, edge.id)),
        documents=documents,
    )


def build_document_records(
    *,
    assets: list[dict[str, str]],
    failures: list[dict[str, str]],
    parts: list[dict[str, str]],
    inventory_by_part: dict[str, dict[str, str]],
    suppliers_by_part: dict[str, list[dict[str, str]]],
    work_orders: list[dict[str, str]],
    assets_by_id: dict[str, dict[str, str]],
    failures_by_code: dict[str, dict[str, str]],
    all_asset_classes: list[str],
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    for asset_class in all_asset_classes:
        documents.append(
            _document(
                doc_id=f"asset_class:{asset_class}",
                page_content=(
                    f"Classe de ativo {asset_class}. Esta classe conecta ativos "
                    "industriais a pecas compativeis para manutencao."
                ),
                metadata={
                    "doc_type": "AssetClass",
                    "asset_class": asset_class,
                    "source_file": "assets.csv;parts.csv",
                },
            )
        )

    for row in assets:
        documents.append(
            _document(
                doc_id=f"asset:{row['asset_id']}",
                page_content=(
                    f"Ativo {row['asset_id']} - {row['name']}. Classe "
                    f"{row['asset_class']}. Localizacao {row['location']}. "
                    f"Criticidade {row['criticality']}. Fabricante "
                    f"{row['manufacturer']}. Comissionado em {row['commissioned_at']}."
                ),
                metadata={
                    "doc_type": "Asset",
                    "asset_id": row["asset_id"],
                    "asset_class": row["asset_class"],
                    "source_file": "assets.csv",
                },
            )
        )

    for row in failures:
        documents.append(
            _document(
                doc_id=f"failure:{row['failure_code']}",
                page_content=(
                    f"Falha {row['failure_code']} - {row['failure_name']}. "
                    f"Sintoma: {row['symptom']}. Causa raiz: {row['root_cause']}. "
                    f"Acao recomendada: {row['recommended_action']}. "
                    f"Severidade: {row['severity']}."
                ),
                metadata={
                    "doc_type": "Failure",
                    "failure_code": row["failure_code"],
                    "severity": row["severity"],
                    "source_file": "failures.csv",
                },
            )
        )

    for row in work_orders:
        asset = assets_by_id[row["asset_id"]]
        failure = failures_by_code[row["failure_code"]]
        documents.append(
            _document(
                doc_id=f"work_order:{row['work_order_id']}",
                page_content=(
                    f"Ordem de servico {row['work_order_id']} para o ativo "
                    f"{asset['asset_id']} - {asset['name']}, classe "
                    f"{asset['asset_class']}, local {asset['location']}. "
                    f"Tipo de manutencao {row['maintenance_type']}. Status "
                    f"{row['status']}. Aberta em {row['opened_at']} e fechada em "
                    f"{row['closed_at'] or 'aberto'}. Falha {failure['failure_code']} "
                    f"- {failure['failure_name']}. Descricao: {row['description']}. "
                    f"Downtime: {row['downtime_hours']} horas."
                ),
                metadata={
                    "doc_type": "WorkOrder",
                    "work_order_id": row["work_order_id"],
                    "asset_id": row["asset_id"],
                    "asset_class": asset["asset_class"],
                    "failure_code": row["failure_code"],
                    "status": row["status"],
                    "maintenance_type": row["maintenance_type"],
                    "source_file": "work_orders.csv",
                },
            )
        )

    for row in parts:
        inventory = inventory_by_part.get(row["part_id"], {})
        suppliers = suppliers_by_part.get(row["part_id"], [])
        supplier_summary = "; ".join(
            f"{supplier['supplier_name']} preferencial={supplier['preferred']} "
            f"entrega_media={supplier['average_delivery_days']} dias "
            f"confiabilidade={supplier['reliability_score']}"
            for supplier in suppliers
        )
        stock_summary = (
            f"Estoque {inventory.get('stock_on_hand')} no "
            f"{inventory.get('warehouse')}, minimo {inventory.get('min_stock')}, "
            f"ponto de reposicao {inventory.get('reorder_point')}."
            if inventory
            else "Sem informacao de estoque."
        )
        for asset_class in parse_compatible_asset_classes(row["compatible_asset_class"]):
            documents.append(
                _document(
                    doc_id=f"part:{row['part_id']}:{asset_class}",
                    page_content=(
                        f"Peca {row['part_id']} - {row['part_name']}. Categoria "
                        f"{row['category']}. Compativel com a classe {asset_class}. "
                        f"Criticidade {row['criticality']}. Lead time "
                        f"{row['lead_time_days']} dias. Custo unitario "
                        f"{row['unit_cost']}. {stock_summary} Fornecedores: "
                        f"{supplier_summary or 'sem fornecedor cadastrado'}."
                    ),
                    metadata={
                        "doc_type": "Part",
                        "part_id": row["part_id"],
                        "asset_class": asset_class,
                        "category": row["category"],
                        "criticality": row["criticality"],
                        "source_file": "parts.csv",
                    },
                )
            )

    for part_id, inventory in inventory_by_part.items():
        documents.append(
            _document(
                doc_id=f"stock:{part_id}:{inventory['warehouse']}",
                page_content=(
                    f"Estoque da peca {part_id} no {inventory['warehouse']}. "
                    f"Saldo atual {inventory['stock_on_hand']}. Estoque minimo "
                    f"{inventory['min_stock']}. Ponto de reposicao "
                    f"{inventory['reorder_point']}. Ultima contagem "
                    f"{inventory['last_counted_at']}."
                ),
                metadata={
                    "doc_type": "Warehouse",
                    "part_id": part_id,
                    "warehouse": inventory["warehouse"],
                    "source_file": "inventory.csv",
                },
            )
        )

    for part_id, suppliers in suppliers_by_part.items():
        for supplier in suppliers:
            documents.append(
                _document(
                    doc_id=f"supplier:{supplier['supplier_id']}:{part_id}",
                    page_content=(
                        f"Fornecedor {supplier['supplier_name']} fornece a peca "
                        f"{part_id}. Preferencial: {supplier['preferred']}. "
                        f"Prazo medio de entrega {supplier['average_delivery_days']} "
                        f"dias. Score de confiabilidade {supplier['reliability_score']}."
                    ),
                    metadata={
                        "doc_type": "Supplier",
                        "supplier_id": supplier["supplier_id"],
                        "supplier_name": supplier["supplier_name"],
                        "part_id": part_id,
                        "source_file": "suppliers.csv",
                    },
                )
            )

    return documents


def write_artifacts(result: GraphBuildResult) -> None:
    NODES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(NODES_PATH, (asdict(node) for node in result.nodes))
    _write_jsonl(EDGES_PATH, (asdict(edge) for edge in result.edges))
    _write_jsonl(DOCUMENTS_PATH, result.documents)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def parse_compatible_asset_classes(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _append_orphans(
    errors: list[str],
    filename: str,
    column: str,
    observed_values: Iterable[str],
    allowed_values: set[str],
) -> None:
    orphans = sorted({value for value in observed_values if value not in allowed_values})
    if orphans:
        errors.append(f"{filename}: {column} sem referencia: {orphans}")


def _candidate_parts_for_asset_class(
    parts: list[dict[str, str]], asset_class: str
) -> list[dict[str, str]]:
    return [
        part
        for part in parts
        if asset_class in parse_compatible_asset_classes(part["compatible_asset_class"])
    ]


def _add_node(
    nodes: dict[str, GraphNode],
    node_type: str,
    key: str,
    properties: dict[str, Any],
) -> None:
    assert_known_node_type(node_type)
    node_id = _node_id(node_type, key)
    nodes[node_id] = GraphNode(
        id=node_id,
        type=node_type,
        key=key,
        properties=_clean_properties(properties),
    )


def _add_edge(
    edges: dict[str, GraphEdge],
    relationship_type: str,
    source: str,
    target: str,
    properties: dict[str, Any],
    qualifier: str | None = None,
) -> None:
    assert_known_relationship_type(relationship_type)
    spec = RELATIONSHIP_TYPES[relationship_type]
    edge_id = _edge_id(source, relationship_type, target, qualifier)
    edges[edge_id] = GraphEdge(
        id=edge_id,
        type=relationship_type,
        source=source,
        target=target,
        provenance=spec.provenance,
        properties=_clean_properties(properties),
    )


def _node_id(node_type: str, key: str) -> str:
    return f"{node_type}:{key}"


def _edge_id(
    source: str, relationship_type: str, target: str, qualifier: str | None = None
) -> str:
    suffix = f":{qualifier}" if qualifier else ""
    return f"{source}-[{relationship_type}]->{target}{suffix}"


def _document(
    doc_id: str,
    page_content: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    clean_metadata = _clean_metadata({**metadata, "doc_id": doc_id})
    return {
        "id": doc_id,
        "page_content": page_content,
        "metadata": clean_metadata,
    }


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _clean_properties(properties: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in properties.items() if value != ""}


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None or value == "":
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = json.dumps(value, ensure_ascii=False)
    return clean


def _parse_date(value: str, field: str, record_id: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DataValidationError(
            [f"Data invalida em {record_id}.{field}: {value}"]
        ) from exc


def _to_int(value: str) -> int:
    return int(value)


def _to_float(value: str) -> float:
    return float(value)


def _to_bool(value: str) -> bool:
    return value.strip().lower() == "true"
