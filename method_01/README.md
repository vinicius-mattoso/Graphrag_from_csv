# Metodo 01: GraphRAG local com LangChain

Esta versao transforma os CSVs de `data/raw` em um grafo local orientado por
ontologia e usa LangChain para embeddings, recuperacao com travessia por
metadados e resposta final com LLM.

Fluxo:

```text
CSV -> ontologia -> grafo JSONL -> documentos LangChain -> Chroma -> GraphRetriever -> LLM
```

## Scripts

Explicacoes detalhadas dos scripts e da arquitetura ficam em
[docs](docs/README.md).

Gerar artefatos e popular Chroma:

```powershell
python -m method_01.script_ingestion
```

Gerar apenas os artefatos JSONL, sem chamar OpenAI:

```powershell
python -m method_01.script_ingestion --skip-vector-store
```

Inspecionar o grafo local:

```powershell
python -m method_01.script_inspection
```

Perguntar ao GraphRAG:

```powershell
python -m method_01.script_ask "quais pecas podem ajudar em queda de pressao no compressor?"
```

## Artefatos

Os arquivos principais ficam em `data/processed/method_01`:

- `graph_nodes.jsonl`
- `graph_edges.jsonl`
- `documents.jsonl`
- `chroma/`

O diretorio `chroma/` e local e deve ficar fora do Git.

## Ontologia

A ontologia esta em `method_01/ontology.py`. Ela define os tipos de nos,
relacionamentos confirmados e o relacionamento inferido `CANDIDATE_PART`.

A relacao `CANDIDATE_PART` e inferida quando a classe do ativo da ordem de
servico aparece em `parts.compatible_asset_class`.

## LangSmith

Todos os scripts carregam `.env` e inicializam as variaveis de tracing. Se
`LANGSMITH_PROJECT` nao estiver definido, o projeto padrao sera
`graphrag-csv-method-01`.
