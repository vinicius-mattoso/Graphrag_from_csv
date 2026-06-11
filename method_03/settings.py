"""Configuracao do Metodo 03."""

from __future__ import annotations

import os
from dataclasses import dataclass

from method_01.settings import (
    DEFAULT_CHAT_MODEL,
    configure_langsmith,
    get_chat_model_name,
    load_environment,
    require_openai_api_key,
)


DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USERNAME = "neo4j"
DEFAULT_NEO4J_DATABASE = "neo4j"
DEFAULT_LANGSMITH_PROJECT = "graphrag-csv-method-03"


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str


def configure_method_03_environment(script_name: str | None = None) -> dict[str, str | None]:
    metadata = configure_langsmith(script_name)
    if (
        not os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGSMITH_PROJECT") == "graphrag-csv-method-01"
    ):
        os.environ["LANGSMITH_PROJECT"] = DEFAULT_LANGSMITH_PROJECT
        metadata["LANGSMITH_PROJECT"] = DEFAULT_LANGSMITH_PROJECT
    return metadata


def get_neo4j_settings(require_password: bool = True) -> Neo4jSettings:
    load_environment()
    password = os.getenv("NEO4J_PASSWORD", "")
    if require_password and not password:
        raise RuntimeError(
            "NEO4J_PASSWORD nao configurado. Defina NEO4J_URI, "
            "NEO4J_USERNAME e NEO4J_PASSWORD no .env antes de usar o Metodo 03."
        )

    return Neo4jSettings(
        uri=os.getenv("NEO4J_URI", DEFAULT_NEO4J_URI),
        username=os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", DEFAULT_NEO4J_USERNAME),
        password=password,
        database=os.getenv("NEO4J_DATABASE", DEFAULT_NEO4J_DATABASE),
    )


def get_neo4j_read_settings(require_password: bool = True) -> Neo4jSettings:
    base = get_neo4j_settings(require_password=require_password)
    read_username = os.getenv("NEO4J_READ_USERNAME") or base.username
    read_password = os.getenv("NEO4J_READ_PASSWORD") or base.password
    if require_password and not read_password:
        raise RuntimeError(
            "NEO4J_READ_PASSWORD/NEO4J_PASSWORD nao configurado para consultas read-only."
        )
    return Neo4jSettings(
        uri=base.uri,
        username=read_username,
        password=read_password,
        database=base.database,
    )


def require_method_03_llm_runtime() -> None:
    require_openai_api_key()


def get_method_03_chat_model_name() -> str:
    return os.getenv("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL) or get_chat_model_name()
