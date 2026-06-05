"""Ontologia explicita da primeira versao do GraphRAG."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeSpec:
    label: str
    key_property: str
    required_properties: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class RelationshipSpec:
    label: str
    source_type: str
    target_type: str
    provenance: str
    required_properties: tuple[str, ...]
    description: str


NODE_TYPES: dict[str, NodeSpec] = {
    "WorkOrder": NodeSpec(
        label="WorkOrder",
        key_property="work_order_id",
        required_properties=(
            "work_order_id",
            "asset_id",
            "failure_code",
            "opened_at",
            "maintenance_type",
            "status",
        ),
        description="Ordem de servico de manutencao.",
    ),
    "Asset": NodeSpec(
        label="Asset",
        key_property="asset_id",
        required_properties=("asset_id", "name", "asset_class", "location"),
        description="Ativo industrial mantido pela operacao.",
    ),
    "AssetClass": NodeSpec(
        label="AssetClass",
        key_property="asset_class",
        required_properties=("asset_class",),
        description="Classe tecnica usada para conectar ativos e pecas.",
    ),
    "Failure": NodeSpec(
        label="Failure",
        key_property="failure_code",
        required_properties=("failure_code", "failure_name", "symptom", "root_cause"),
        description="Modo de falha ou codigo de falha.",
    ),
    "Part": NodeSpec(
        label="Part",
        key_property="part_id",
        required_properties=("part_id", "part_name", "compatible_asset_class"),
        description="Peca sobressalente ou item tecnico.",
    ),
    "Supplier": NodeSpec(
        label="Supplier",
        key_property="supplier_name",
        required_properties=("supplier_name",),
        description="Fornecedor deduplicado por nome comercial.",
    ),
    "Warehouse": NodeSpec(
        label="Warehouse",
        key_property="warehouse",
        required_properties=("warehouse",),
        description="Almoxarifado onde pecas sao estocadas.",
    ),
}


RELATIONSHIP_TYPES: dict[str, RelationshipSpec] = {
    "FOR_ASSET": RelationshipSpec(
        label="FOR_ASSET",
        source_type="WorkOrder",
        target_type="Asset",
        provenance="confirmed",
        required_properties=("join_key", "source_file"),
        description="Ordem de servico executada para um ativo.",
    ),
    "HAS_FAILURE": RelationshipSpec(
        label="HAS_FAILURE",
        source_type="WorkOrder",
        target_type="Failure",
        provenance="confirmed",
        required_properties=("join_key", "source_file"),
        description="Ordem de servico associada a um modo de falha.",
    ),
    "HAS_CLASS": RelationshipSpec(
        label="HAS_CLASS",
        source_type="Asset",
        target_type="AssetClass",
        provenance="confirmed",
        required_properties=("join_key", "source_file"),
        description="Ativo pertence a uma classe tecnica.",
    ),
    "COMPATIBLE_WITH": RelationshipSpec(
        label="COMPATIBLE_WITH",
        source_type="Part",
        target_type="AssetClass",
        provenance="confirmed",
        required_properties=("source_column", "source_file"),
        description="Peca declarada como compativel com uma classe de ativo.",
    ),
    "SUPPLIES": RelationshipSpec(
        label="SUPPLIES",
        source_type="Supplier",
        target_type="Part",
        provenance="confirmed",
        required_properties=("supplier_id", "source_file"),
        description="Fornecedor comercializa uma peca.",
    ),
    "STOCKED_AT": RelationshipSpec(
        label="STOCKED_AT",
        source_type="Part",
        target_type="Warehouse",
        provenance="confirmed",
        required_properties=("stock_on_hand", "warehouse", "source_file"),
        description="Peca possui saldo em um almoxarifado.",
    ),
    "CANDIDATE_PART": RelationshipSpec(
        label="CANDIDATE_PART",
        source_type="WorkOrder",
        target_type="Part",
        provenance="inferred",
        required_properties=("asset_class", "inference_rule"),
        description="Peca candidata inferida por classe de ativo compativel.",
    ),
}


CONFIRMED_RELATIONSHIPS = frozenset(
    label
    for label, spec in RELATIONSHIP_TYPES.items()
    if spec.provenance == "confirmed"
)
INFERRED_RELATIONSHIPS = frozenset(
    label
    for label, spec in RELATIONSHIP_TYPES.items()
    if spec.provenance == "inferred"
)


CSV_REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "assets.csv": (
        "asset_id",
        "name",
        "asset_class",
        "location",
        "criticality",
        "manufacturer",
        "commissioned_at",
    ),
    "failures.csv": (
        "failure_code",
        "failure_name",
        "symptom",
        "root_cause",
        "recommended_action",
        "severity",
    ),
    "inventory.csv": (
        "part_id",
        "warehouse",
        "stock_on_hand",
        "min_stock",
        "reorder_point",
        "last_counted_at",
    ),
    "parts.csv": (
        "part_id",
        "part_name",
        "category",
        "compatible_asset_class",
        "criticality",
        "lead_time_days",
        "unit_cost",
    ),
    "suppliers.csv": (
        "supplier_id",
        "supplier_name",
        "part_id",
        "preferred",
        "average_delivery_days",
        "reliability_score",
    ),
    "work_orders.csv": (
        "work_order_id",
        "asset_id",
        "opened_at",
        "closed_at",
        "maintenance_type",
        "failure_code",
        "status",
        "downtime_hours",
        "description",
    ),
}


PRIMARY_KEYS: dict[str, str] = {
    "assets.csv": "asset_id",
    "failures.csv": "failure_code",
    "inventory.csv": "part_id",
    "parts.csv": "part_id",
    "suppliers.csv": "supplier_id",
    "work_orders.csv": "work_order_id",
}


def assert_known_node_type(node_type: str) -> None:
    if node_type not in NODE_TYPES:
        raise ValueError(f"Tipo de no fora da ontologia: {node_type}")


def assert_known_relationship_type(relationship_type: str) -> None:
    if relationship_type not in RELATIONSHIP_TYPES:
        raise ValueError(f"Relacionamento fora da ontologia: {relationship_type}")
