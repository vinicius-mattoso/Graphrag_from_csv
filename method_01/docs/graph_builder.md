# graph_builder.py

`graph_builder.py` e o modulo que transforma CSVs em artefatos GraphRAG.

Ele nao chama OpenAI, Chroma ou LLM. Isso e importante: a construcao do grafo
fica deterministica e testavel.

## Responsabilidades

- Ler todos os CSVs obrigatorios.
- Validar estrutura e integridade.
- Criar nos conforme `ontology.py`.
- Criar arestas confirmadas.
- Criar arestas inferidas `CANDIDATE_PART`.
- Criar documentos textuais para o RAG.
- Salvar artefatos JSONL.

## Fluxo interno

```text
read_csv_tables()
    |
    v
validate_raw_tables()
    |
    v
build_graph()
    |
    +--> GraphNode[]
    +--> GraphEdge[]
    +--> document_records[]
    |
    v
write_artifacts()
```

## Validacoes

`validate_raw_tables()` checa:

- existencia dos CSVs;
- colunas obrigatorias;
- chaves primarias vazias;
- chaves primarias duplicadas;
- `work_orders.asset_id` apontando para `assets.asset_id`;
- `work_orders.failure_code` apontando para `failures.failure_code`;
- `inventory.part_id` apontando para `parts.part_id`;
- `suppliers.part_id` apontando para `parts.part_id`;
- classes de ativos em `parts.compatible_asset_class`;
- datas de abertura e fechamento das ordens.

Se houver erro, o modulo levanta `DataValidationError`.

## Artefatos gerados

### graph_nodes.jsonl

Cada linha representa um no:

```json
{"id": "Asset:A-100", "type": "Asset", "key": "A-100", "properties": {...}}
```

### graph_edges.jsonl

Cada linha representa uma aresta:

```json
{"type": "CANDIDATE_PART", "source": "WorkOrder:WO-1001", "target": "Part:P-001", "provenance": "inferred", "properties": {...}}
```

### documents.jsonl

Cada linha representa um documento para recuperacao:

```json
{"id": "part:P-001:BOMBA_CENTRIFUGA", "page_content": "...", "metadata": {...}}
```

## Como os documentos sao montados

`build_document_records()` cria documentos para:

- classes de ativos;
- ativos;
- falhas;
- ordens de servico;
- pecas por classe compativel;
- estoque;
- fornecedores.

Esses documentos sao textos curtos e densos. A ideia e carregar no texto aquilo
que ajuda o embedding e carregar nos metadados aquilo que ajuda a travessia.

## Relacao com GraphRAG

Este modulo cria a ponte entre dados estruturados e recuperacao textual.

- O grafo vira `graph_nodes.jsonl` e `graph_edges.jsonl`.
- O RAG recebe `documents.jsonl`.
- Os documentos preservam IDs e metadados do grafo.

Assim, o retriever consegue misturar similaridade textual com relacoes
estruturais.
