"""Validacao defensiva de Cypher gerado por LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from method_03.schema import (
    allowed_labels,
    allowed_relationships,
    properties_for_label,
    properties_for_relationship,
)


FORBIDDEN_PHRASES = (
    "CREATE INDEX",
    "CREATE CONSTRAINT",
    "DROP INDEX",
    "DROP CONSTRAINT",
    "LOAD CSV",
)

FORBIDDEN_WORDS = (
    "CREATE",
    "MERGE",
    "DELETE",
    "DETACH",
    "SET",
    "REMOVE",
    "DROP",
    "CALL",
    "APOC",
    "FOREACH",
    "USE",
)

UNSUPPORTED_READ_WORDS = (
    "UNWIND",
    "UNION",
    "PROFILE",
    "EXPLAIN",
    "SHOW",
    "YIELD",
)

NODE_PATTERN = re.compile(r"\(\s*([A-Za-z_][A-Za-z0-9_]*)?\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
REL_PATTERN = re.compile(r"\[\s*([A-Za-z_][A-Za-z0-9_]*)?\s*:\s*([A-Za-z_][A-Za-z0-9_]*)")
PROPERTY_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")
LIMIT_PATTERN = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ValidationResult:
    cypher: str
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class CypherValidationError(RuntimeError):
    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        super().__init__("\n".join(result.errors))


def validate_cypher(cypher: str, max_rows: int = 50) -> ValidationResult:
    normalized = _normalize_cypher(cypher)
    errors: list[str] = []
    warnings: list[str] = []

    if not normalized:
        errors.append("Cypher vazio.")
        return ValidationResult(normalized, False, errors, warnings)

    upper = normalized.upper()
    if ";" in normalized:
        errors.append("Multiplas statements ou ponto e virgula nao sao permitidos.")
    if "`" in normalized:
        errors.append("Identificadores com crase nao sao permitidos.")
    if "|" in normalized:
        errors.append("Alternancia de labels/relacionamentos nao e permitida.")
    if "//" in normalized or "/*" in normalized or "*/" in normalized:
        errors.append("Comentarios Cypher nao sao permitidos em queries geradas.")
    if not upper.startswith(("MATCH ", "OPTIONAL MATCH ")):
        errors.append("A query deve comecar com MATCH ou OPTIONAL MATCH.")
    if not re.search(r"\bRETURN\b", upper):
        errors.append("A query deve conter RETURN.")

    _append_forbidden_errors(upper, errors)
    _append_schema_errors(normalized, errors)
    normalized = _enforce_limit(normalized, max_rows, errors, warnings)

    return ValidationResult(normalized, not errors, errors, warnings)


def require_valid_cypher(cypher: str, max_rows: int = 50) -> ValidationResult:
    result = validate_cypher(cypher, max_rows=max_rows)
    if not result.is_valid:
        raise CypherValidationError(result)
    return result


def _normalize_cypher(cypher: str) -> str:
    return "\n".join(line.rstrip() for line in cypher.strip().splitlines()).strip()


def _append_forbidden_errors(upper: str, errors: list[str]) -> None:
    for phrase in FORBIDDEN_PHRASES:
        if phrase in upper:
            errors.append(f"Comando proibido encontrado: {phrase}.")
    for word in FORBIDDEN_WORDS + UNSUPPORTED_READ_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", upper):
            errors.append(f"Palavra-chave nao permitida: {word}.")


def _append_schema_errors(cypher: str, errors: list[str]) -> None:
    node_aliases: dict[str, str] = {}
    relationship_aliases: dict[str, str] = {}
    labels = allowed_labels()
    relationships = allowed_relationships()

    node_matches = NODE_PATTERN.findall(cypher)
    relationship_matches = REL_PATTERN.findall(cypher)

    if not node_matches and not relationship_matches:
        errors.append("A query deve usar pelo menos um label ou relacionamento da ontologia.")

    for alias, label in node_matches:
        if label not in labels:
            errors.append(f"Label fora da ontologia: {label}.")
        if alias:
            node_aliases[alias] = label

    for alias, relationship_type in relationship_matches:
        if relationship_type not in relationships:
            errors.append(f"Relacionamento fora da ontologia: {relationship_type}.")
        if alias:
            relationship_aliases[alias] = relationship_type

    for alias, property_name in PROPERTY_PATTERN.findall(cypher):
        if alias in node_aliases:
            label = node_aliases[alias]
            if property_name not in properties_for_label(label):
                errors.append(
                    f"Propriedade {alias}.{property_name} nao existe no label {label}."
                )
        elif alias in relationship_aliases:
            relationship_type = relationship_aliases[alias]
            if property_name not in properties_for_relationship(relationship_type):
                errors.append(
                    "Propriedade "
                    f"{alias}.{property_name} nao existe em {relationship_type}."
                )


def _enforce_limit(
    cypher: str,
    max_rows: int,
    errors: list[str],
    warnings: list[str],
) -> str:
    matches = list(LIMIT_PATTERN.finditer(cypher))
    if not matches:
        errors.append("A query deve conter LIMIT.")
        return cypher

    last_match = matches[-1]
    limit_value = int(last_match.group(1))
    if limit_value <= max_rows:
        return cypher

    warnings.append(f"LIMIT {limit_value} reduzido para {max_rows}.")
    start, end = last_match.span(1)
    return f"{cypher[:start]}{max_rows}{cypher[end:]}"


def format_validation(result: ValidationResult) -> str:
    if result.is_valid:
        lines = ["Validacao: OK"]
        lines.extend(f"Aviso: {warning}" for warning in result.warnings)
        return "\n".join(lines)
    lines = ["Validacao: falhou"]
    lines.extend(f"- {error}" for error in result.errors)
    return "\n".join(lines)


def coerce_parameters(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
