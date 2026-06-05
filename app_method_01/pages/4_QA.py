from __future__ import annotations

import traceback

import streamlit as st

from app_method_01.app_utils import (
    APP_TITLE,
    artifact_status,
    configure_app_environment,
    load_documents,
)
from method_01.script_ask import (
    _answer_with_llm,
    _build_graph_retriever,
    _format_context,
    _format_sources,
)
from method_01.settings import CHROMA_DIR, require_openai_api_key


st.set_page_config(page_title=f"{APP_TITLE} | Q&A", page_icon=":material/question_answer:", layout="wide")
configure_app_environment("app_method_01.qa")

st.title("Q&A")
st.caption("Pergunte sobre os CSVs usando GraphRetriever + ChatOpenAI.")

status = artifact_status()
documents = load_documents()

top_cols = st.columns(4)
top_cols[0].metric("Documentos", len(documents))
top_cols[1].metric("Chroma", "OK" if status["chroma_exists"] else "Ausente")
top_cols[2].metric("OpenAI key", "OK" if status["openai_key"] else "Ausente")
top_cols[3].metric("Modelo", status["chat_model"])

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

with st.form("qa_form"):
    question = st.text_area(
        "Pergunta",
        value="quais pecas podem ajudar em queda de pressao no compressor?",
        height=95,
    )
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
    k = col_a.slider("k", min_value=2, max_value=20, value=8)
    start_k = col_b.slider("start_k", min_value=1, max_value=10, value=4)
    max_depth = col_c.slider("max_depth", min_value=0, max_value=4, value=2)
    show_context = col_d.checkbox("Mostrar contexto", value=True)
    submitted = st.form_submit_button("Perguntar", use_container_width=True)

if submitted:
    try:
        require_openai_api_key()
        if not CHROMA_DIR.exists():
            raise RuntimeError("Chroma nao encontrado. Rode a ingestao completa primeiro.")

        with st.spinner("Recuperando contexto e gerando resposta..."):
            from method_01.vector_store import load_vector_store

            vector_store = load_vector_store()
            retriever = _build_graph_retriever(
                vector_store=vector_store,
                k=k,
                start_k=start_k,
                max_depth=max_depth,
            )
            docs = retriever.invoke(question)
            answer = _answer_with_llm(question, docs)
            sources = _format_sources(docs)
            context = _format_context(docs)

        st.session_state.qa_history.insert(
            0,
            {
                "question": question,
                "answer": answer,
                "sources": sources,
                "context": context,
            },
        )
        st.success("Resposta gerada.")
    except Exception as exc:
        st.error(str(exc))
        st.code(traceback.format_exc())

if st.session_state.qa_history:
    latest = st.session_state.qa_history[0]
    st.subheader("Resposta")
    st.markdown(latest["answer"])

    st.subheader("Fontes")
    for source in latest["sources"]:
        st.write(f"- {source}")

    if show_context:
        with st.expander("Contexto recuperado", expanded=True):
            st.code(latest["context"])

    with st.expander("Historico da sessao"):
        for index, item in enumerate(st.session_state.qa_history, start=1):
            st.write(f"**{index}. {item['question']}**")
            st.write(item["answer"])
else:
    st.info("Envie uma pergunta para ver resposta, fontes e contexto.")
