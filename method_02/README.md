# Metodo 02: GraphRAG com Neo4j

Este metodo transforma os CSVs em um grafo persistente no Neo4j e usa uma
estrategia hibrida:

```text
CSV -> ontologia -> Neo4j -> vector index -> Cypher/subgrafo -> LLM
```

Documentacao complementar: [docs](docs/README.md).

## Diferenca para o Metodo 01

| Metodo | Grafo | Busca semantica | Travessia |
| --- | --- | --- | --- |
| `method_01` | JSONL local | Chroma | Metadados no GraphRetriever |
| `method_02` | Neo4j | Neo4j Vector Index | Cypher em grafo real |

## Subir Neo4j local

Exemplo com Docker:

```powershell
docker run --name neo4j-graphrag-csv `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/password `
  neo4j:5
```

Configure `.env`:

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
NEO4J_VECTOR_INDEX=graphrag_document_embeddings
NEO4J_FULLTEXT_INDEX=graphrag_document_fulltext
NEO4J_VECTOR_DIMENSIONS=1536
```

## Scripts

Ingerir grafo e documentos sem embeddings:

```powershell
python -m method_02.script_ingestion --reset --skip-embeddings
```

Ingerir grafo, documentos e embeddings no Neo4j Vector Index:

```powershell
python -m method_02.script_ingestion --reset
```

Inspecionar contagens no Neo4j:

```powershell
python -m method_02.script_inspection
```

Recuperar subgrafo sem chamar LLM:

```powershell
python -m method_02.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --no-llm
```

Perguntar com resposta final da LLM:

```powershell
python -m method_02.script_ask "quais pecas podem ajudar em queda de pressao no compressor?" --show-context
```

## Modelo de dados

Os nos e arestas seguem a mesma ontologia conceitual do Metodo 01:

- `WorkOrder`, `Asset`, `AssetClass`, `Failure`, `Part`, `Supplier`, `Warehouse`;
- `FOR_ASSET`, `HAS_FAILURE`, `HAS_CLASS`, `COMPATIBLE_WITH`, `SUPPLIES`, `STOCKED_AT`;
- `CANDIDATE_PART` como aresta inferida.

O Metodo 02 tambem cria nos `GraphDocument`, que guardam:

- `doc_id`;
- `page_content`;
- `embedding`;
- metadados como `asset_class`, `failure_code`, `part_id`, `work_order_id`.

Esses documentos sao ligados aos nos do dominio por relacoes como `DESCRIBES`,
`MENTIONS_CLASS` e `MENTIONS_PART`.

## Recuperacao

O fluxo de pergunta e:

```text
1. Embed da pergunta.
2. Neo4j Vector Index retorna documentos semanticamente proximos.
3. O sistema extrai sementes como failure_code e asset_class.
4. Cypher controlado expande o subgrafo de manutencao.
5. A LLM responde com base no contexto retornado do Neo4j.
```

Para a pergunta de queda de pressao no compressor, o subgrafo esperado passa por:

```text
F-QUEDA_PRESSAO -> WO-1003 -> A-200 -> COMPRESSOR_AR -> P-003/P-006
```
