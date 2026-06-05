from __future__ import annotations

import streamlit as st

from app_method_01.app_utils import (
    APP_TITLE,
    artifact_status,
    chroma_summary,
    configure_app_environment,
    count_by,
    load_documents,
    load_edges,
    load_nodes,
)
from method_01.settings import PROJECT_ROOT


st.set_page_config(page_title=APP_TITLE, page_icon=":material/account_tree:", layout="wide")
configure_app_environment("app_method_01.home")

st.title("Method 01 - GraphRAG CSV")
st.caption("Exploracao local da ingestao, grafo, documentos, vector store e Q&A.")

status = artifact_status()
nodes = load_nodes()
edges = load_edges()
documents = load_documents()

metric_cols = st.columns(6)
metric_cols[0].metric("CSVs brutos", status["raw_csv_count"])
metric_cols[1].metric("Nos", len(nodes))
metric_cols[2].metric("Arestas", len(edges))
metric_cols[3].metric("Documentos", len(documents))
metric_cols[4].metric("Chroma", chroma_summary())
metric_cols[5].metric("OpenAI key", "OK" if status["openai_key"] else "Ausente")

st.divider()

left, right = st.columns([1.35, 1])

with left:
    st.subheader("Fluxo da arquitetura")
    svg_path = PROJECT_ROOT / "method_01" / "docs" / "graphrag_flow.svg"
    if svg_path.exists():
        st.image(str(svg_path), use_container_width=True)
    else:
        st.warning("Diagrama SVG nao encontrado.")

with right:
    st.subheader("Estado atual")
    st.write(
        {
            "processed_dir": str(status["processed_dir"]),
            "nodes_jsonl": status["nodes_exists"],
            "edges_jsonl": status["edges_exists"],
            "documents_jsonl": status["documents_exists"],
            "chroma": status["chroma_exists"],
            "chat_model": status["chat_model"],
            "embedding_model": status["embedding_model"],
        }
    )

    if nodes:
        st.write("Nos por tipo")
        st.dataframe(count_by(nodes, "type"), use_container_width=True, hide_index=True)
    if edges:
        st.write("Arestas por tipo")
        st.dataframe(count_by(edges, "type"), use_container_width=True, hide_index=True)

st.divider()

st.subheader("Infograficos executivos")
info_tab_1, info_tab_2 = st.tabs(["Pipeline", "Pergunta e subgrafo"])

with info_tab_1:
    infographic_path = (
        PROJECT_ROOT
        / "method_01"
        / "docs"
        / "infographic_pipeline_executive.svg"
    )
    if infographic_path.exists():
        st.image(str(infographic_path), use_container_width=True)
    else:
        st.warning("Infografico do pipeline nao encontrado.")

with info_tab_2:
    question_infographic_path = (
        PROJECT_ROOT
        / "method_01"
        / "docs"
        / "infographic_question_retrieval.svg"
    )
    if question_infographic_path.exists():
        st.image(str(question_infographic_path), use_container_width=True)
    else:
        st.warning("Infografico da pergunta nao encontrado.")

st.divider()
st.subheader("Como usar")
st.code(
    "streamlit run app_method_01/Home.py\n"
    "python -m method_01.script_ingestion --skip-vector-store\n"
    "python -m method_01.script_ingestion",
    language="powershell",
)
