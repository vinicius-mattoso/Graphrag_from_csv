"""Configuracao do Metodo 02."""

from __future__ import annotations

import os
from dataclasses import dataclass

from method_01.settings import (
    DEFAULT_EMBEDDING_MODEL,
    load_environment,
    require_openai_api_key,
)


DEFAULT_NEO4J_URI = "bolt://localhost:7687"
DEFAULT_NEO4J_USERNAME = "neo4j"
DEFAULT_NEO4J_DATABASE = "neo4j"
DEFAULT_VECTOR_INDEX_NAME = "graphrag_document_embeddings"
DEFAULT_FULLTEXT_INDEX_NAME = "graphrag_document_fulltext"
DEFAULT_EMBEDDING_DIMENSION = 1536
DEFAULT_LANGSMITH_PROJECT = "graphrag-csv-method-02"


@dataclass(frozen=True)
class Neo4jSettings:
    uri: str
    username: str
    password: str
    database: str
    vector_index_name: str
    fulltext_index_name: str
    embedding_dimension: int
    embedding_model: str


def configure_method_02_environment(script_name: str | None = None) -> dict[str, str | None]:
    load_environment()

    if os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGSMITH_API_KEY"):
        os.environ["LANGSMITH_API_KEY"] = os.environ["LANGCHAIN_API_KEY"]

    if os.getenv("LANGCHAIN_TRACING_V2") and not os.getenv("LANGSMITH_TRACING"):
        os.environ["LANGSMITH_TRACING"] = os.environ["LANGCHAIN_TRACING_V2"]

    if not os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGSMITH_PROJECT") == "graphrag-csv-method-01":
        os.environ["LANGSMITH_PROJECT"] = DEFAULT_LANGSMITH_PROJECT

    return {
        "script_name": script_name,
        "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING"),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2"),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT"),
    }


def get_neo4j_settings(require_password: bool = True) -> Neo4jSettings:
    load_environment()
    password = os.getenv("NEO4J_PASSWORD", "")
    if require_password and not password:
        raise RuntimeError(
            "NEO4J_PASSWORD nao configurado. Defina NEO4J_URI, "
            "NEO4J_USERNAME e NEO4J_PASSWORD no .env antes de usar o Metodo 02."
        )

    return Neo4jSettings(
        uri=os.getenv("NEO4J_URI", DEFAULT_NEO4J_URI),
        username=os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", DEFAULT_NEO4J_USERNAME),
        password=password,
        database=os.getenv("NEO4J_DATABASE", DEFAULT_NEO4J_DATABASE),
        vector_index_name=os.getenv("NEO4J_VECTOR_INDEX", DEFAULT_VECTOR_INDEX_NAME),
        fulltext_index_name=os.getenv("NEO4J_FULLTEXT_INDEX", DEFAULT_FULLTEXT_INDEX_NAME),
        embedding_dimension=int(os.getenv("NEO4J_VECTOR_DIMENSIONS", DEFAULT_EMBEDDING_DIMENSION)),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
    )


def require_method_02_runtime() -> Neo4jSettings:
    require_openai_api_key()
    return get_neo4j_settings(require_password=True)
