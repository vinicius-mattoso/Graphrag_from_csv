"""Schema controlado exposto ao gerador Text2Cypher."""

from __future__ import annotations

from method_01.ontology import NODE_TYPES, RELATIONSHIP_TYPES


NODE_PROPERTIES: dict[str, tuple[str, ...]] = {
    "WorkOrder": (
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
    "Asset": (
        "asset_id",
        "name",
        "asset_class",
        "location",
        "criticality",
        "manufacturer",
        "commissioned_at",
    ),
    "AssetClass": ("asset_class", "source_files"),
    "Failure": (
        "failure_code",
        "failure_name",
        "symptom",
        "root_cause",
        "recommended_action",
        "severity",
    ),
    "Part": (
        "part_id",
        "part_name",
        "category",
        "compatible_asset_class",
        "compatible_asset_classes",
        "criticality",
        "lead_time_days",
        "unit_cost",
    ),
    "Supplier": ("supplier_name", "supplier_ids"),
    "Warehouse": ("warehouse",),
}


RELATIONSHIP_PROPERTIES: dict[str, tuple[str, ...]] = {
    "FOR_ASSET": ("join_key", "source_file", "asset_id"),
    "HAS_FAILURE": ("join_key", "source_file", "failure_code"),
    "HAS_CLASS": ("join_key", "source_file", "asset_class"),
    "COMPATIBLE_WITH": ("source_column", "source_file", "asset_class"),
    "SUPPLIES": (
        "supplier_id",
        "supplier_name",
        "preferred",
        "average_delivery_days",
        "reliability_score",
        "source_file",
    ),
    "STOCKED_AT": (
        "warehouse",
        "stock_on_hand",
        "min_stock",
        "reorder_point",
        "last_counted_at",
        "source_file",
    ),
    "CANDIDATE_PART": (
        "asset_class",
        "inference_rule",
        "source_work_order_id",
        "part_id",
        "confidence",
    ),
}


TEXT2CYPHER_EXAMPLES = [
    {
        "question": "quais pecas estao abaixo do estoque minimo?",
        "cypher": """
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
WHERE stock.stock_on_hand < stock.min_stock
RETURN
  p.part_id AS part_id,
  p.part_name AS part_name,
  p.criticality AS criticality,
  w.warehouse AS warehouse,
  stock.stock_on_hand AS stock_on_hand,
  stock.min_stock AS min_stock,
  stock.reorder_point AS reorder_point
ORDER BY stock.stock_on_hand ASC, part_id
LIMIT 50
""".strip(),
        "parameters": {},
    },
    {
        "question": "quais fornecedores atendem pecas criticas?",
        "cypher": """
MATCH (supplier:Supplier)-[supply:SUPPLIES]->(part:Part)
WHERE part.criticality = $criticality
RETURN
  supplier.supplier_name AS supplier_name,
  part.part_id AS part_id,
  part.part_name AS part_name,
  supply.preferred AS preferred,
  supply.average_delivery_days AS average_delivery_days,
  supply.reliability_score AS reliability_score
ORDER BY supplier_name, part_id
LIMIT 50
""".strip(),
        "parameters": {"criticality": "Alta"},
    },
    {
        "question": "quais falhas aparecem em bombas centrifugas?",
        "cypher": """
MATCH (wo:WorkOrder)-[:HAS_FAILURE]->(failure:Failure)
MATCH (wo)-[:FOR_ASSET]->(asset:Asset)-[:HAS_CLASS]->(asset_class:AssetClass)
WHERE asset_class.asset_class = $asset_class
RETURN DISTINCT
  failure.failure_code AS failure_code,
  failure.failure_name AS failure_name,
  failure.root_cause AS root_cause,
  failure.recommended_action AS recommended_action
ORDER BY failure_code
LIMIT 50
""".strip(),
        "parameters": {"asset_class": "BOMBA_CENTRIFUGA"},
    },
    {
        "question": "quais ordens tiveram maior downtime?",
        "cypher": """
MATCH (wo:WorkOrder)-[:FOR_ASSET]->(asset:Asset)
RETURN
  wo.work_order_id AS work_order_id,
  asset.asset_id AS asset_id,
  asset.name AS asset_name,
  wo.downtime_hours AS downtime_hours,
  wo.status AS status
ORDER BY downtime_hours DESC
LIMIT 50
""".strip(),
        "parameters": {},
    },
]


def allowed_labels() -> set[str]:
    return set(NODE_TYPES)


def allowed_relationships() -> set[str]:
    return set(RELATIONSHIP_TYPES)


def properties_for_label(label: str) -> set[str]:
    return set(NODE_PROPERTIES.get(label, ()))


def properties_for_relationship(relationship_type: str) -> set[str]:
    return set(RELATIONSHIP_PROPERTIES.get(relationship_type, ()))


def build_schema_text() -> str:
    lines = ["Labels e propriedades permitidas:"]
    for label in sorted(NODE_TYPES):
        properties = ", ".join(NODE_PROPERTIES[label])
        lines.append(f"- {label}: {properties}")

    lines.append("")
    lines.append("Relacionamentos e propriedades permitidas:")
    for relationship_type, spec in sorted(RELATIONSHIP_TYPES.items()):
        properties = ", ".join(RELATIONSHIP_PROPERTIES[relationship_type])
        lines.append(
            f"- (:{spec.source_type})-[:{relationship_type}]->(:{spec.target_type}) "
            f"props: {properties}"
        )

    lines.append("")
    lines.append(
        "Observacao: dados de estoque ficam na relacao STOCKED_AT, "
        "nao no no Warehouse."
    )
    return "\n".join(lines)


def build_examples_text() -> str:
    blocks = []
    for index, example in enumerate(TEXT2CYPHER_EXAMPLES, start=1):
        blocks.append(
            "\n".join(
                [
                    f"Exemplo {index}",
                    f"Pergunta: {example['question']}",
                    "Cypher:",
                    example["cypher"],
                    f"Parametros: {example['parameters']}",
                ]
            )
        )
    return "\n\n".join(blocks)
