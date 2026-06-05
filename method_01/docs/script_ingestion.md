# script_ingestion.py

Comando:

```powershell
python -m method_01.script_ingestion
```

Modo sem OpenAI/Chroma:

```powershell
python -m method_01.script_ingestion --skip-vector-store
```

## Objetivo

Este script cria a base do GraphRAG. Ele transforma os CSVs brutos em grafo,
documentos de recuperacao e, no modo completo, em um indice vetorial Chroma.

## Entrada

Le os CSVs em `data/raw`:

- `assets.csv`
- `failures.csv`
- `inventory.csv`
- `parts.csv`
- `suppliers.csv`
- `work_orders.csv`

## Processamento

1. Inicializa LangSmith tracing com `configure_langsmith`.
2. Exige `OPENAI_API_KEY`, exceto quando `--skip-vector-store` e usado.
3. Chama `build_graph()` em `graph_builder.py`.
4. Valida chaves, colunas obrigatorias, referencias e datas.
5. Aplica a ontologia definida em `ontology.py`.
6. Gera nos, arestas e documentos.
7. Salva JSONL com `write_artifacts()`.
8. No modo completo, chama `build_vector_store()` em `vector_store.py`.

## Saida

Gera em `data/processed/method_01`:

- `graph_nodes.jsonl`: nos normalizados da ontologia.
- `graph_edges.jsonl`: relacionamentos confirmados e inferidos.
- `documents.jsonl`: documentos que serao indexados e recuperados.
- `chroma/`: indice vetorial local persistente.

## Papel na arquitetura GraphRAG

Este script corresponde a fase de indexacao. Ele e responsavel por construir o
"Graph" antes de construir o "RAG".

A decisao importante da v1 e que o grafo nao e extraido pelo LLM. Ele e gerado
de forma deterministica:

- IDs e chaves dos CSVs geram arestas confirmadas.
- A compatibilidade entre classe do ativo e classe compativel da peca gera a
  aresta inferida `CANDIDATE_PART`.
- Os documentos LangChain recebem metadados planos para permitir travessia pelo
  `GraphRetriever`.

## Quando usar

Use sempre que:

- os CSVs em `data/raw` mudarem;
- a ontologia mudar;
- os documentos de recuperacao forem alterados;
- for necessario recriar o indice Chroma.
