from __future__ import annotations

import traceback

import pandas as pd
import streamlit as st

from app_method_01.app_utils import (
    APP_TITLE,
    artifact_status,
    configure_app_environment,
)
from method_01.graph_builder import (
    DataValidationError,
    build_graph,
    read_csv_tables,
    validate_raw_tables,
    write_artifacts,
)
from method_01.settings import (
    CHROMA_DIR,
    DOCUMENTS_PATH,
    EDGES_PATH,
    NODES_PATH,
    RAW_DATA_DIR,
    require_openai_api_key,
)


st.set_page_config(page_title=f"{APP_TITLE} | Ingestao", page_icon=":material/input:", layout="wide")
configure_app_environment("app_method_01.ingestao")

st.title("Ingestao")
st.caption("Valide CSVs, gere artefatos JSONL e opcionalmente popule o Chroma local.")

status = artifact_status()

top_cols = st.columns(4)
top_cols[0].metric("CSVs brutos", status["raw_csv_count"])
top_cols[1].metric("graph_nodes.jsonl", "OK" if status["nodes_exists"] else "Ausente")
top_cols[2].metric("documents.jsonl", "OK" if status["documents_exists"] else "Ausente")
top_cols[3].metric("Chroma", "OK" if status["chroma_exists"] else "Ausente")

st.subheader("Arquivos brutos")
raw_files = [{"arquivo": path.name, "tamanho_bytes": path.stat().st_size} for path in status["raw_files"]]
st.dataframe(pd.DataFrame(raw_files), use_container_width=True, hide_index=True)

with st.expander("Preview dos CSVs"):
    for csv_path in status["raw_files"]:
        st.write(f"`{csv_path.name}`")
        st.dataframe(pd.read_csv(csv_path).head(20), use_container_width=True)

st.divider()
action_cols = st.columns(3)

with action_cols[0]:
    if st.button("Validar CSVs", use_container_width=True):
        try:
            tables = read_csv_tables(RAW_DATA_DIR)
            validate_raw_tables(tables)
            st.success("CSVs validos para a ontologia atual.")
        except (DataValidationError, FileNotFoundError) as exc:
            st.error(str(exc))

with action_cols[1]:
    if st.button("Gerar JSONL", use_container_width=True):
        try:
            with st.spinner("Construindo grafo e documentos..."):
                result = build_graph()
                write_artifacts(result)
            st.success("Artefatos JSONL gerados.")
            st.write(
                {
                    "nodes": len(result.nodes),
                    "edges": len(result.edges),
                    "documents": len(result.documents),
                    "nodes_path": str(NODES_PATH),
                    "edges_path": str(EDGES_PATH),
                    "documents_path": str(DOCUMENTS_PATH),
                }
            )
        except Exception as exc:
            st.error(str(exc))
            st.code(traceback.format_exc())

with action_cols[2]:
    if st.button("Gerar JSONL + Chroma", use_container_width=True):
        try:
            require_openai_api_key()
            with st.spinner("Construindo grafo, documentos e Chroma..."):
                result = build_graph()
                write_artifacts(result)
                from method_01.vector_store import build_vector_store

                indexed_count = build_vector_store(result.documents)
            st.success("Indice completo gerado.")
            st.write(
                {
                    "nodes": len(result.nodes),
                    "edges": len(result.edges),
                    "documents": len(result.documents),
                    "indexed_documents": indexed_count,
                    "chroma_dir": str(CHROMA_DIR),
                }
            )
        except Exception as exc:
            st.error(str(exc))
            st.code(traceback.format_exc())

st.divider()
st.subheader("Comandos equivalentes")
st.code(
    "python -m method_01.script_ingestion --skip-vector-store\n"
    "python -m method_01.script_ingestion",
    language="powershell",
)
