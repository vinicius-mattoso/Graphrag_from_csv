# Explicacao do monolito do Metodo 03

O arquivo `method_03/monolith.py` e uma versao didatica do Metodo 03. Ele junta
em um unico script o que, no restante do pacote, fica separado em modulos.

A ideia nao e ser a melhor arquitetura para producao. A ideia e permitir ler o
fluxo completo de ponta a ponta em um unico lugar.

Ilustracoes do fluxo de resposta:

- [monolith_langchain_response_flow.svg](monolith_langchain_response_flow.svg):
  resposta usando `GraphCypherQAChain`.
- [monolith_custom_response_flow.svg](monolith_custom_response_flow.svg):
  resposta usando os modulos locais do Metodo 03.

## Como executar

Fluxo padrao, usando o Text2Cypher pronto do LangChain:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset
```

Fluxo alternativo, usando a implementacao local de Text2Cypher:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset --engine custom
```

O parametro `--reset` remove os dados antigos marcados como `method_03` antes de
gravar novamente o grafo no Neo4j.

## O que o monolito faz

O fluxo principal executa estas etapas:

```text
1. Valida ambiente
2. Le CSVs e constroi o grafo em memoria
3. Grava nos e arestas no Neo4j
4. Gera Cypher a partir da pergunta
5. Valida a query gerada
6. Executa a query validada no Neo4j
7. Gera a resposta final com LLM
```

Essas etapas aparecem no terminal com numeros para facilitar o acompanhamento.

## Etapa 1: validar ambiente

O monolito carrega o `.env` e verifica se existe `OPENAI_API_KEY`, porque a LLM
e usada para gerar Cypher e gerar a resposta final.

Tambem carrega as variaveis do Neo4j:

```text
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
NEO4J_DATABASE
```

Quando usa a engine LangChain para consulta, ele tambem respeita:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

Se essas variaveis read-only nao existirem, ele usa as credenciais normais do
Neo4j.

## Etapa 2: construir o grafo em memoria

O monolito chama:

```python
build_graph()
```

Essa funcao vem de `method_01.graph_builder`. Ela le os CSVs em `data/raw`,
valida as chaves e monta:

- nos de dominio;
- arestas de dominio;
- documentos textuais, embora o monolito do Metodo 03 use principalmente nos e
  arestas.

O monolito reaproveita esse construtor para manter a mesma ontologia dos outros
metodos.

## Etapa 3: gravar no Neo4j

Depois de construir o grafo, o monolito chama:

```python
ingest_graph_to_neo4j(...)
```

Essa funcao cria constraints basicas e grava:

- `GraphNode` + label de dominio, como `Part`, `Failure` e `WorkOrder`;
- relacionamentos como `FOR_ASSET`, `HAS_FAILURE`, `STOCKED_AT` e
  `CANDIDATE_PART`.

O campo `source_system = "method_03"` permite apagar apenas os dados deste
metodo quando `--reset` e usado.

## Engine padrao: LangChain

Por padrao, o monolito usa:

```python
GraphCypherQAChain
Neo4jGraph
ChatOpenAI
```

Esse caminho esta em:

```python
_run_langchain_graph_cypher_chain(...)
```

O LangChain faz duas coisas:

- gera uma query Cypher a partir da pergunta;
- usa o resultado do Neo4j para gerar a resposta final.

O monolito ainda passa exemplos few-shot para a chain usando:

```python
build_examples_text()
```

E limita o schema enviado para a chain usando apenas labels e relacionamentos da
ontologia:

```python
include_types=sorted(allowed_labels() | allowed_relationships())
```

Isso evita que a LLM use detalhes tecnicos que nao fazem parte do dominio.

## Validacao mesmo usando LangChain

Mesmo usando `GraphCypherQAChain`, o monolito nao deixa a query executar sem
controle.

Ele cria uma classe interna:

```python
ValidatedNeo4jGraph(Neo4jGraph)
```

Essa classe sobrescreve o metodo:

```python
query(...)
```

Antes de executar no Neo4j, ela chama:

```python
require_valid_cypher(...)
```

Isso significa que a query gerada pelo LangChain ainda passa pelo validador local
do projeto.

O validador bloqueia, por exemplo:

```text
CREATE
MERGE
DELETE
DETACH
SET
REMOVE
DROP
CALL
APOC
LOAD CSV
;
```

Tambem exige que a query use a ontologia conhecida e tenha `LIMIT`.

## Engine alternativa: custom

Com `--engine custom`, o monolito nao usa `GraphCypherQAChain`.

Ele chama diretamente os modulos locais:

```python
generate_cypher(...)
require_valid_cypher(...)
run_read_query(...)
generate_answer(...)
```

Esse caminho e mais explicito para estudar cada etapa:

- `text2cypher.py` gera a query;
- `validator.py` valida a query;
- `neo4j_store.py` executa a query;
- `retrieval.py` gera a resposta final.

## Quando usar cada engine

Use `--engine langchain` quando quiser ver como o framework pronto resolve
Text2Cypher com menos codigo.

Use `--engine custom` quando quiser entender exatamente como o projeto monta o
prompt, interpreta a resposta da LLM, valida o Cypher e executa no Neo4j.

## Resumo

O monolito existe para estudo.

Ele mostra que o Metodo 03 tem duas formas de fazer Text2Cypher:

```text
LangChain GraphCypherQAChain
ou
Implementacao local controlada
```

Nos dois casos, a regra central permanece:

```text
A LLM pode propor Cypher.
O sistema valida.
O Neo4j executa somente se a query for segura.
```



python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset --engine custom
1. Validando ambiente
   Neo4j: neo4j+s://c699a04d.databases.neo4j.io database=c699a04d
2. Lendo CSVs e construindo grafo em memoria
   Nos: 34 | Arestas: 55
3. Gravando grafo no Neo4j
   Gravado: 34 nos, 55 arestas
4. Gerando Cypher com LLM pelos modulos locais
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse) WHERE stock.stock_on_hand < stock.min_stock RETURN p.part_id AS part_id, p.part_name AS part_name, p.criticality AS criticality, w.warehouse AS warehouse, stock.stock_on_hand AS stock_on_hand, stock.min_stock AS min_stock, stock.reorder_point AS reorder_point ORDER BY stock.stock_on_hand ASC, part_id LIMIT 50
5. Validando Cypher
Validacao: OK
6. Executando Cypher validado no Neo4j
[
  {
    "part_id": "P-006",
    "part_name": "Valvula retencao DN50",
    "criticality": "Alta",
    "warehouse": "Almoxarifado Utilidades",
    "stock_on_hand": 0,
    "min_stock": 2,
    "reorder_point": 4
  },
  {
    "part_id": "P-003",
    "part_name": "Filtro coalescente 1pol",
    "criticality": "Alta",
    "warehouse": "Almoxarifado Utilidades",
    "stock_on_hand": 1,
    "min_stock": 3,
    "reorder_point": 5
  },
  {
    "part_id": "P-001",
    "part_name": "Selo mecanico 32mm",
    "criticality": "Alta",
    "warehouse": "Almoxarifado Central",
    "stock_on_hand": 3,
    "min_stock": 5,
    "reorder_point": 8
  }
]
7. Gerando resposta final com LLM
As peças que estão abaixo do estoque mínimo são:

1. **ID da peça:** P-006
   - **Nome da peça:** Válvula retenção DN50
   - **Criticidade:** Alta
   - **Armazém:** Almoxarifado Utilidades
   - **Estoque disponível:** 0
   - **Estoque mínimo:** 2
   - **Ponto de reabastecimento:** 4

2. **ID da peça:** P-003
   - **Nome da peça:** Filtro coalescente 1pol
   - **Criticidade:** Alta
   - **Armazém:** Almoxarifado Utilidades
   - **Estoque disponível:** 1
   - **Estoque mínimo:** 3
   - **Ponto de reabastecimento:** 5

3. **ID da peça:** P-001
   - **Nome da peça:** Selo mecânico 32mm
   - **Criticidade:** Alta
   - **Armazém:** Almoxarifado Central
   - **Estoque disponível:** 3
   - **Estoque mínimo:** 5
   - **Ponto de reabastecimento:** 8
