"""Configuracao compartilhada dos scripts do metodo 01."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "method_01"
CHROMA_DIR = PROCESSED_DIR / "chroma"

NODES_PATH = PROCESSED_DIR / "graph_nodes.jsonl"
EDGES_PATH = PROCESSED_DIR / "graph_edges.jsonl"
DOCUMENTS_PATH = PROCESSED_DIR / "documents.jsonl"

CHROMA_COLLECTION = "graphrag_csv_method_01"
DEFAULT_LANGSMITH_PROJECT = "graphrag-csv-method-01"
DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _load_dotenv_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_environment() -> None:
    if os.getenv("METHOD_01_DISABLE_DOTENV") == "1":
        return

    env_path = PROJECT_ROOT / ".env"
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        _load_dotenv_fallback(env_path)
        return

    load_dotenv(env_path)


def configure_langsmith(script_name: str | None = None) -> dict[str, str | None]:
    """Load .env and normalize LangSmith/LangChain tracing variables."""

    load_environment()

    if os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGSMITH_API_KEY"):
        os.environ["LANGSMITH_API_KEY"] = os.environ["LANGCHAIN_API_KEY"]

    if os.getenv("LANGCHAIN_TRACING_V2") and not os.getenv("LANGSMITH_TRACING"):
        os.environ["LANGSMITH_TRACING"] = os.environ["LANGCHAIN_TRACING_V2"]

    if not os.getenv("LANGSMITH_PROJECT"):
        os.environ["LANGSMITH_PROJECT"] = DEFAULT_LANGSMITH_PROJECT

    metadata = {
        "script_name": script_name,
        "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING"),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2"),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT"),
    }
    return metadata


def get_chat_model_name() -> str:
    return os.getenv("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL)


def get_embedding_model_name() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def require_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY nao configurada. Crie um arquivo .env a partir de "
            ".env.example ou defina a variavel no ambiente antes de executar "
            "este script."
        )
