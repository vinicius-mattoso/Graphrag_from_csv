# Documentacao do Metodo 01

Esta pasta explica como cada script participa da arquitetura GraphRAG local.

## Arquitetura e componentes

- [graphrag_flow.svg](graphrag_flow.svg): diagrama visual do fluxo completo.
- [architecture.md](architecture.md): arquitetura completa do metodo.
- [ontology.md](ontology.md): ontologia, tipos de nos e relacionamentos.
- [graph_builder.md](graph_builder.md): transformacao dos CSVs em grafo e documentos.
- [vector_store.md](vector_store.md): Chroma, embeddings e GraphRetriever.

## Papel de cada script

- [script_ingestion.md](script_ingestion.md): cria a base GraphRAG.
- [script_ask.md](script_ask.md): consulta a base GraphRAG.
- [script_inspection.md](script_inspection.md): audita os artefatos gerados.

## Interface local

O app Streamlit fica em `app_method_01` e permite explorar ingestao, grafo,
documentos e Q&A em uma interface multipage.

## Relacao com GraphRAG

Nesta v1, "Graph" e "RAG" aparecem em camadas separadas:

- A camada de grafo vem da ontologia e das arestas geradas a partir dos CSVs.
- A camada RAG vem dos documentos indexados no Chroma com embeddings.
- A ponte entre as duas e o `GraphRetriever`, que parte da similaridade vetorial
  e atravessa documentos relacionados por metadados como `asset_class`,
  `asset_id`, `failure_code`, `part_id` e `warehouse`.

Isso mantem a v1 didatica: o grafo e explicito, rastreavel e inspecionavel antes
de qualquer chamada ao LLM.
