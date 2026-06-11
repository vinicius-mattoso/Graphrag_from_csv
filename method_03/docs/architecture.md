# Arquitetura do Metodo 03

O Metodo 03 implementa GraphRAG com Neo4j e Text2Cypher. A diferenca principal
para os metodos anteriores e que a pergunta do usuario pode virar uma consulta
Cypher dinamica, desde que essa consulta passe por validacao.

## Objetivo

Permitir perguntas mais variadas sobre o grafo de manutencao industrial sem
criar uma query fixa para cada caso.

Exemplos:

```text
quais pecas estao abaixo do estoque minimo?
quais fornecedores atendem pecas criticas?
quais falhas aparecem em bombas centrifugas?
quais ordens tiveram maior downtime?
```

## Fluxo geral

```text
CSV
  |
  v
method_01.graph_builder
  |
  v
nos e arestas em memoria
  |
  v
Neo4j
  |
  v
pergunta do usuario
  |
  v
schema + exemplos + regras
  |
  v
LLM gera Cypher
  |
  v
validador local
  |
  v
Neo4j executa query read-only
  |
  v
resultados estruturados
  |
  v
LLM gera resposta final
```

## Componentes principais

| Componente | Papel |
| --- | --- |
| `settings.py` | Carrega `.env`, OpenAI, Neo4j e credenciais read-only |
| `schema.py` | Define schema controlado e exemplos few-shot |
| `text2cypher.py` | Gera Cypher usando prompt local |
| `validator.py` | Bloqueia Cypher perigoso ou fora da ontologia |
| `neo4j_store.py` | Grava grafo no Neo4j e executa queries |
| `retrieval.py` | Orquestra pergunta, query, validacao, execucao e resposta |
| `script_ingestion.py` | CLI para ingerir CSVs no Neo4j |
| `script_inspection.py` | CLI para inspecionar o grafo |
| `script_ask.py` | CLI principal de perguntas |
| `monolith.py` | Versao didatica do fluxo completo |

## Ingestao

O Metodo 03 reaproveita:

```python
method_01.graph_builder.build_graph()
```

Isso evita duplicar a logica de leitura dos CSVs e garante que a ontologia usada
no Metodo 03 seja a mesma do Metodo 01.

A ingestao grava no Neo4j:

- nos com label tecnico `GraphNode`;
- labels de dominio, como `WorkOrder`, `Asset`, `Failure`, `Part`;
- propriedades originais dos CSVs;
- relacionamentos da ontologia, como `FOR_ASSET`, `HAS_FAILURE`,
  `COMPATIBLE_WITH`, `STOCKED_AT` e `SUPPLIES`.

O Metodo 03 nao depende de vector index para responder. Ele usa o grafo
estruturado e Cypher.

## Text2Cypher

Existem dois caminhos de Text2Cypher.

O caminho principal do pacote usa os modulos locais:

```text
script_ask.py -> retrieval.py -> text2cypher.py -> validator.py -> neo4j_store.py
```

Esse caminho e mais controlado, porque a query e gerada primeiro, validada em
seguida e so depois executada.

O monolito tambem possui um caminho com framework pronto:

```text
monolith.py --engine langchain
```

Esse caminho usa:

```python
langchain_neo4j.GraphCypherQAChain
```

Mesmo nesse caso, o projeto envolve o `Neo4jGraph.query()` com o validador local
antes de executar qualquer Cypher.

## Schema controlado

O schema enviado para a LLM fica em `schema.py`.

Labels principais:

```text
WorkOrder
Asset
AssetClass
Failure
Part
Supplier
Warehouse
```

Relacionamentos principais:

```text
FOR_ASSET
HAS_FAILURE
HAS_CLASS
COMPATIBLE_WITH
SUPPLIES
STOCKED_AT
CANDIDATE_PART
```

Uma decisao importante: propriedades de estoque ficam no relacionamento
`STOCKED_AT`, nao no no `Warehouse`.

Por isso, uma query correta para estoque usa:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
WHERE stock.stock_on_hand < stock.min_stock
RETURN p.part_id, w.warehouse, stock.stock_on_hand, stock.min_stock
LIMIT 50
```

## Validacao

O validador em `validator.py` e a camada central de seguranca da aplicacao.

Ele bloqueia comandos de escrita ou risco operacional:

```text
CREATE
MERGE
DELETE
DETACH
SET
REMOVE
DROP
LOAD CSV
CALL
APOC
FOREACH
USE
```

Tambem bloqueia:

```text
;
comentarios
identificadores com crase
labels fora da ontologia
relacionamentos fora da ontologia
propriedades inexistentes em aliases tipados
queries sem LIMIT
full graph scan sem label ou relacionamento tipado
```

Esse validador nao substitui permissoes no banco. Ele reduz risco na aplicacao.

## Credenciais read-only

Para consulta, o Metodo 03 pode usar:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

Se essas variaveis nao existirem, ele usa:

```text
NEO4J_USERNAME
NEO4J_PASSWORD
```

Em um ambiente real, a recomendacao e criar um usuario Neo4j somente leitura para
as perguntas Text2Cypher. Assim, mesmo que uma query perigosa escape do
validador, o banco bloqueia alteracoes.

## CLIs

Ingerir dados:

```powershell
python -m method_03.script_ingestion --reset
```

Inspecionar:

```powershell
python -m method_03.script_inspection
```

Perguntar:

```powershell
python -m method_03.script_ask "quais pecas estao abaixo do estoque minimo?" --show-cypher --show-context
```

Rodar o monolito:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset
```

Comparar com engine custom:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset --engine custom
```

## Limites

O Metodo 03 e mais flexivel, mas menos deterministico que uma consulta Cypher
fixa.

Principais limites:

- a LLM pode gerar Cypher invalido;
- a query pode ser sintaticamente valida, mas semanticamente fraca;
- a validacao por regex nao e um parser Cypher completo;
- o usuario Neo4j read-only ainda e necessario;
- respostas devem ser auditadas pelo Cypher gerado e pelas linhas retornadas.

## Resumo

O Metodo 03 troca uma recuperacao fixa por uma recuperacao dinamica:

```text
Pergunta -> Text2Cypher -> Validacao -> Neo4j -> Resposta
```

O ganho e flexibilidade.

O custo e a necessidade de guardrails fortes, schema controlado e credenciais
read-only.
