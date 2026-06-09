# Arquitetura do Metodo 02

O Metodo 02 usa Neo4j como camada persistente de grafo. Ele ainda parte dos
mesmos CSVs e da mesma ontologia conceitual, mas a recuperacao passa a usar
Cypher sobre um grafo real.

## Fluxo

```text
data/raw/*.csv
    |
    v
method_01.graph_builder
    |
    +--> nos e arestas
    +--> documentos textuais
    |
    v
Neo4j
    |
    +--> constraints e indexes
    +--> GraphNode + labels de dominio
    +--> GraphDocument com embedding
    +--> relacoes reais
    |
    v
Neo4j Vector Index -> sementes -> Cypher -> subgrafo -> LLM
```

## O que fica no Neo4j

- Nos de dominio: ativos, falhas, pecas, ordens, classes, fornecedores e
  almoxarifados.
- Arestas de dominio: relacoes confirmadas e inferidas.
- Nos `GraphDocument`: textos usados na busca semantica.
- Relacoes documento-dominio: `DESCRIBES`, `MENTIONS_CLASS`, `MENTIONS_PART`.

## Por que isso e diferente do Metodo 01

No Metodo 01, a travessia acontece por metadados indexados no Chroma. No Metodo
02, a travessia acontece em Cypher, sobre relacoes persistidas no Neo4j.

Isso permite:

- inspecionar o grafo em Neo4j Browser;
- escrever consultas Cypher controladas;
- combinar vector search e pattern matching;
- evoluir para perguntas multi-hop mais complexas.

## Limites da v1 do Metodo 02

- A extracao de grafo ainda e deterministica.
- O LLM nao cria Cypher livremente.
- A consulta de subgrafo e controlada para o dominio de manutencao.
- O vector index e usado para encontrar sementes, nao para substituir o grafo.
