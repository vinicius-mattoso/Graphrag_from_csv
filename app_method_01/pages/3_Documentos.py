from __future__ import annotations

import streamlit as st

from app_method_01.app_utils import (
    APP_TITLE,
    configure_app_environment,
    count_by,
    filter_by_text,
    load_documents,
    records_to_dataframe,
)


st.set_page_config(page_title=f"{APP_TITLE} | Documentos", page_icon=":material/article:", layout="wide")
configure_app_environment("app_method_01.documentos")

st.title("Documentos")
st.caption("Explore os documentos enviados ao vector store e seus metadados.")

documents = load_documents()

if not documents:
    st.warning("documents.jsonl nao encontrado. Gere primeiro em Ingestao.")
    st.stop()

cols = st.columns(4)
cols[0].metric("Documentos", len(documents))
cols[1].metric("Tipos", len({doc["metadata"].get("doc_type") for doc in documents}))
cols[2].metric("Com asset_class", sum(1 for doc in documents if "asset_class" in doc["metadata"]))
cols[3].metric("Com part_id", sum(1 for doc in documents if "part_id" in doc["metadata"]))

left, right = st.columns([0.8, 1.2])
with left:
    st.write("Documentos por tipo")
    by_type = [
        {"type": row["name"], "count": row["count"]}
        for row in count_by([doc["metadata"] for doc in documents], "doc_type").to_dict("records")
    ]
    st.dataframe(by_type, use_container_width=True, hide_index=True)

with right:
    doc_types = sorted({doc["metadata"].get("doc_type", "missing") for doc in documents})
    selected_types = st.multiselect("Filtrar tipo", doc_types, default=doc_types)
    query = st.text_input("Buscar nos documentos", placeholder="Ex.: queda de pressao, P-006, COMPRESSOR_AR")
    filtered_documents = [
        doc for doc in documents if doc["metadata"].get("doc_type", "missing") in selected_types
    ]
    filtered_documents = filter_by_text(
        filtered_documents,
        query,
        ("id", "page_content", "metadata"),
    )
    st.dataframe(records_to_dataframe(filtered_documents), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Detalhe")
doc_options = [doc["id"] for doc in filtered_documents]
if doc_options:
    selected_id = st.selectbox("Selecionar documento", doc_options)
    selected_doc = next(doc for doc in filtered_documents if doc["id"] == selected_id)
    st.write("Metadados")
    st.json(selected_doc["metadata"])
    st.write("Conteudo")
    st.write(selected_doc["page_content"])
else:
    st.info("Nenhum documento nos filtros atuais.")
