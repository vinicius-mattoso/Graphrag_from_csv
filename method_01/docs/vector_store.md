# vector_store.py

`vector_store.py` encapsula a parte LangChain relacionada a embeddings, Chroma e
preparacao dos documentos para GraphRetriever.

## Responsabilidades

- Converter registros de `documents.jsonl` em `Document` do LangChain.
- Criar embeddings com `OpenAIEmbeddings`.
- Criar ou carregar o Chroma local.
- Aplicar `ShreddingTransformer` antes de indexar.
- Definir os metadados usados como arestas de travessia no GraphRetriever.

## Chroma como vector storage

Nesta v1, Chroma e o armazenamento vetorial local. Ele guarda:

- texto do documento;
- embedding;
- metadados planos;
- colecao `graphrag_csv_method_01`.

O diretorio padrao e:

```text
data/processed/method_01/chroma/
```

Esse diretorio e ignorado pelo Git porque e um artefato local.

## Embeddings

Os embeddings usam `OpenAIEmbeddings` com o modelo configurado em:

```text
OPENAI_EMBEDDING_MODEL
```

Se a variavel nao estiver definida, o default do projeto e:

```text
text-embedding-3-small
```

## GRAPH_RETRIEVER_EDGES

O modulo define:

```python
GRAPH_RETRIEVER_EDGES = [
    ("asset_class", "asset_class"),
    ("asset_id", "asset_id"),
    ("failure_code", "failure_code"),
    ("part_id", "part_id"),
    ("warehouse", "warehouse"),
]
```

Essas tuplas dizem ao GraphRetriever quais metadados funcionam como links entre
documentos.

Exemplo:

- um documento de ordem tem `asset_class=BOMBA_CENTRIFUGA`;
- um documento de peca tambem tem `asset_class=BOMBA_CENTRIFUGA`;
- o GraphRetriever pode atravessar de um documento para o outro por esse valor.

## Por que usar ShreddingTransformer?

O GraphRetriever precisa trabalhar bem com metadados em vector stores. O
`ShreddingTransformer` prepara os documentos para que os metadados usados como
arestas sejam indexados de forma compativel com Chroma.

## Relacao com GraphRAG

O vector store e a camada "RAG" do projeto. Ele permite encontrar documentos por
similaridade semantica.

O GraphRetriever adiciona a camada "Graph" sobre esse vector store, expandindo
resultados por metadados conectados.

Portanto:

- Chroma responde "quais documentos parecem semanticamente proximos?".
- GraphRetriever responde "quais documentos proximos tambem estao conectados?".
- O LLM recebe o contexto final para gerar a resposta.
