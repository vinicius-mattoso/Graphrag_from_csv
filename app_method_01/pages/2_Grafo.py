from __future__ import annotations

import streamlit as st

from app_method_01.app_utils import (
    APP_TITLE,
    configure_app_environment,
    count_by,
    filter_by_text,
    graph_to_dot,
    load_edges,
    load_nodes,
    records_to_dataframe,
)


st.set_page_config(page_title=f"{APP_TITLE} | Grafo", page_icon=":material/hub:", layout="wide")
configure_app_environment("app_method_01.grafo")

st.title("Grafo")
st.caption("Explore nos, arestas, proveniencia e uma visualizacao compacta do grafo.")

nodes = load_nodes()
edges = load_edges()

if not nodes or not edges:
    st.warning("Artefatos nao encontrados. Gere primeiro em Ingestao.")
    st.stop()

cols = st.columns(5)
cols[0].metric("Nos", len(nodes))
cols[1].metric("Arestas", len(edges))
cols[2].metric("Tipos de no", len({node["type"] for node in nodes}))
cols[3].metric("Tipos de aresta", len({edge["type"] for edge in edges}))
cols[4].metric("Inferidas", sum(1 for edge in edges if edge.get("provenance") == "inferred"))

tab_nodes, tab_edges, tab_visual = st.tabs(["Nos", "Arestas", "Visualizacao"])

with tab_nodes:
    left, right = st.columns([0.85, 1.15])
    with left:
        st.write("Nos por tipo")
        st.dataframe(count_by(nodes, "type"), use_container_width=True, hide_index=True)
    with right:
        node_types = sorted({node["type"] for node in nodes})
        selected_types = st.multiselect("Filtrar tipos de no", node_types, default=node_types)
        node_query = st.text_input("Buscar nos", placeholder="Ex.: A-200, COMPRESSOR_AR, Part")
        filtered_nodes = [node for node in nodes if node["type"] in selected_types]
        filtered_nodes = filter_by_text(filtered_nodes, node_query, ("id", "type", "key", "properties"))
        st.dataframe(records_to_dataframe(filtered_nodes), use_container_width=True, hide_index=True)

with tab_edges:
    left, right = st.columns([0.85, 1.15])
    with left:
        st.write("Arestas por tipo")
        st.dataframe(count_by(edges, "type"), use_container_width=True, hide_index=True)
        st.write("Arestas por proveniencia")
        st.dataframe(count_by(edges, "provenance"), use_container_width=True, hide_index=True)
    with right:
        edge_types = sorted({edge["type"] for edge in edges})
        provenances = sorted({edge["provenance"] for edge in edges})
        selected_edge_types = st.multiselect("Filtrar tipos de aresta", edge_types, default=edge_types)
        selected_provenances = st.multiselect("Filtrar proveniencia", provenances, default=provenances)
        edge_query = st.text_input("Buscar arestas", placeholder="Ex.: WO-1003, P-006, CANDIDATE_PART")
        filtered_edges = [
            edge
            for edge in edges
            if edge["type"] in selected_edge_types and edge["provenance"] in selected_provenances
        ]
        filtered_edges = filter_by_text(
            filtered_edges,
            edge_query,
            ("id", "type", "source", "target", "provenance", "properties"),
        )
        st.dataframe(records_to_dataframe(filtered_edges), use_container_width=True, hide_index=True)

with tab_visual:
    st.write("Visualizacao compacta por filtros")
    visual_cols = st.columns(3)
    visual_node_types = visual_cols[0].multiselect(
        "Tipos de no no diagrama",
        sorted({node["type"] for node in nodes}),
        default=["WorkOrder", "Asset", "Failure", "Part"],
    )
    visual_edge_types = visual_cols[1].multiselect(
        "Tipos de aresta no diagrama",
        sorted({edge["type"] for edge in edges}),
        default=["FOR_ASSET", "HAS_FAILURE", "CANDIDATE_PART"],
    )
    max_edges = visual_cols[2].slider("Maximo de arestas", min_value=10, max_value=120, value=60, step=10)

    visual_nodes = [node for node in nodes if node["type"] in visual_node_types]
    visual_node_ids = {node["id"] for node in visual_nodes}
    visual_edges = [
        edge
        for edge in edges
        if edge["type"] in visual_edge_types
        and edge["source"] in visual_node_ids
        and edge["target"] in visual_node_ids
    ]
    st.graphviz_chart(graph_to_dot(visual_nodes, visual_edges, max_edges=max_edges), use_container_width=True)
