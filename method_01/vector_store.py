"""Adaptadores LangChain para documentos e Chroma."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from method_01.settings import (
    CHROMA_COLLECTION,
    CHROMA_DIR,
    get_embedding_model_name,
)


GRAPH_RETRIEVER_EDGES = [
    ("asset_class", "asset_class"),
    ("asset_id", "asset_id"),
    ("failure_code", "failure_code"),
    ("part_id", "part_id"),
    ("warehouse", "warehouse"),
]


def build_vector_store(
    document_records: list[dict[str, Any]],
    persist_directory: Path = CHROMA_DIR,
    reset: bool = True,
) -> int:
    """Populate a persistent Chroma vector store from document records."""

    if reset and persist_directory.exists():
        shutil.rmtree(persist_directory)
    persist_directory.mkdir(parents=True, exist_ok=True)

    patch_chromadb_include_enum()
    embeddings = _openai_embeddings()
    vector_store = _new_chroma(embeddings, persist_directory)
    documents = _to_langchain_documents(document_records)

    try:
        from langchain_graph_retriever.transformers import ShreddingTransformer
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale langchain-graph-retriever[chroma] "
            "para indexar documentos com metadados compativeis com GraphRetriever."
        ) from exc

    documents_to_index = list(ShreddingTransformer().transform_documents(documents))
    vector_store.add_documents(documents_to_index)

    persist = getattr(vector_store, "persist", None)
    if callable(persist):
        persist()

    close = getattr(vector_store, "close", None)
    if callable(close):
        close()

    return len(documents_to_index)


def load_vector_store(persist_directory: Path = CHROMA_DIR):
    patch_chromadb_include_enum()
    embeddings = _openai_embeddings()
    return _new_chroma(embeddings, persist_directory)


def patch_chromadb_include_enum() -> None:
    """Patch Chroma >=1.5 for langchain-graph-retriever 0.8.0.

    The Chroma adapter in langchain-graph-retriever imports
    chromadb.api.types.IncludeEnum, which was removed in newer Chroma releases.
    Chroma still accepts the same include values as strings, so this shim restores
    the expected attributes without changing runtime behavior.
    """

    try:
        import chromadb.api.types as chroma_types
    except (ImportError, ModuleNotFoundError):
        return

    if hasattr(chroma_types, "IncludeEnum"):
        return

    class IncludeEnum:
        documents = "documents"
        embeddings = "embeddings"
        metadatas = "metadatas"
        distances = "distances"
        uris = "uris"
        data = "data"

    chroma_types.IncludeEnum = IncludeEnum


def _openai_embeddings():
    try:
        from langchain_openai import OpenAIEmbeddings
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale langchain-openai antes de usar "
            "embeddings OpenAI."
        ) from exc

    return OpenAIEmbeddings(model=get_embedding_model_name())


def _new_chroma(embeddings, persist_directory: Path):
    try:
        from langchain_chroma import Chroma
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale langchain-chroma antes de usar "
            "o vector store local."
        ) from exc

    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )


def _to_langchain_documents(document_records: list[dict[str, Any]]):
    try:
        from langchain_core.documents import Document
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependencia ausente: instale langchain-core/langchain antes de "
            "converter documentos."
        ) from exc

    documents = []
    for record in document_records:
        documents.append(
            Document(
                id=record["id"],
                page_content=record["page_content"],
                metadata=record["metadata"],
            )
        )
    return documents
