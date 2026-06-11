# Validacao na versao LangChain do monolito

Este documento explica como o monolito do Metodo 03 usa
`langchain_neo4j.GraphCypherQAChain` sem deixar a query gerada chegar
diretamente ao Neo4j.

O ponto central e:

```text
LangChain gera Cypher.
O projeto intercepta a query.
O validador local decide se pode executar.
So depois o Neo4j recebe a query.
```

## Onde isso acontece

No monolito, o fluxo LangChain fica em:

```python
_run_langchain_graph_cypher_chain(...)
```

Dentro dessa funcao, o codigo cria uma classe local:

```python
class ValidatedNeo4jGraph(Neo4jGraph):
    def query(...):
        validation = require_valid_cypher(query, max_rows=max_rows)
        return super().query(validation.cypher, ...)
```

Essa classe herda de `Neo4jGraph`, mas sobrescreve o metodo `query`.

Isso e importante porque o `GraphCypherQAChain` executa Cypher chamando:

```python
graph.query(generated_cypher)
```

Como o grafo usado pela chain e `ValidatedNeo4jGraph`, toda query gerada pelo
LangChain passa primeiro por:

```python
require_valid_cypher(...)
```

Se a query falhar, uma excecao `CypherValidationError` e levantada e a query nao
e executada.

## Fluxo completo da versao LangChain

```text
Pergunta do usuario
  |
  v
GraphCypherQAChain
  |
  v
LLM gera Cypher
  |
  v
ValidatedNeo4jGraph.query()
  |
  v
require_valid_cypher()
  |
  +--> se falhar: bloqueia
  |
  +--> se passar: chama Neo4jGraph.query()
                  |
                  v
                Neo4j
```

## O que vem do LangChain

O LangChain fornece:

- `GraphCypherQAChain`: chain que gera Cypher e depois gera a resposta final;
- `Neo4jGraph`: wrapper de conexao com Neo4j;
- `validate_cypher=True`: corretor estrutural de direcao de relacionamento;
- `include_types`: filtro de tipos que entram no schema enviado para a chain.

No monolito:

```python
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    cypher_prompt=cypher_prompt,
    include_types=sorted(allowed_labels() | allowed_relationships()),
    validate_cypher=True,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
    top_k=max_rows,
)
```

O `include_types` reduz o schema que a LLM ve. Assim, ela recebe os labels e
relacionamentos de dominio, nao detalhes tecnicos desnecessarios.

Mesmo assim, isso nao e suficiente como seguranca. Por isso existe o wrapper com
`ValidatedNeo4jGraph`.

## Como labels sao conferidos

O validador local esta em:

```python
method_03/validator.py
```

Ele usa uma regex para encontrar labels em padroes Cypher como:

```cypher
(p:Part)
(wo:WorkOrder)
(failure:Failure)
```

Internamente, ele compara cada label encontrado com:

```python
allowed_labels()
```

Essa funcao vem de `schema.py` e retorna os labels definidos pela ontologia:

```text
WorkOrder
Asset
AssetClass
Failure
Part
Supplier
Warehouse
```

Se a LLM gerar algo como:

```cypher
MATCH (x:Customer)
RETURN x
LIMIT 50
```

o validador registra erro:

```text
Label fora da ontologia: Customer.
```

## Como relacionamentos sao conferidos

O validador tambem procura relacionamentos em padroes como:

```cypher
[stock:STOCKED_AT]
[:HAS_FAILURE]
[:FOR_ASSET]
```

Cada relacionamento encontrado e comparado com:

```python
allowed_relationships()
```

Relacionamentos permitidos:

```text
FOR_ASSET
HAS_FAILURE
HAS_CLASS
COMPATIBLE_WITH
SUPPLIES
STOCKED_AT
CANDIDATE_PART
```

Se a LLM gerar:

```cypher
MATCH (a:Asset)-[:OWNS]->(p:Part)
RETURN a, p
LIMIT 50
```

o validador bloqueia porque `OWNS` nao esta na ontologia.

## Como propriedades sao conferidas

O validador detecta propriedades no formato:

```cypher
alias.propriedade
```

Exemplos:

```cypher
p.part_id
stock.stock_on_hand
w.warehouse
```

Para conferir a propriedade, ele primeiro identifica o tipo do alias:

```cypher
(p:Part)
[stock:STOCKED_AT]
(w:Warehouse)
```

Depois compara a propriedade com os dicionarios em `schema.py`:

```python
NODE_PROPERTIES
RELATIONSHIP_PROPERTIES
```

Exemplo correto:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
RETURN p.part_id, stock.stock_on_hand, w.warehouse
LIMIT 50
```

Exemplo bloqueado:

```cypher
MATCH (w:Warehouse)
RETURN w.stock_on_hand
LIMIT 50
```

Nesse modelo, `stock_on_hand` nao e propriedade de `Warehouse`. Ela fica no
relacionamento `STOCKED_AT`. Portanto a query deve usar:

```cypher
stock.stock_on_hand
```

## Como comandos perigosos sao bloqueados

O validador transforma a query para maiusculas em uma variavel auxiliar e procura
palavras proibidas.

Lista principal:

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
FOREACH
USE
```

Tambem bloqueia frases especificas:

```text
CREATE INDEX
CREATE CONSTRAINT
DROP INDEX
DROP CONSTRAINT
LOAD CSV
```

Exemplo bloqueado:

```cypher
MATCH (p:Part)
DELETE p
RETURN p
LIMIT 50
```

Motivo:

```text
Palavra-chave nao permitida: DELETE.
```

Outro exemplo bloqueado:

```cypher
MATCH (p:Part)
SET p.reviewed = true
RETURN p
LIMIT 50
```

Motivo:

```text
Palavra-chave nao permitida: SET.
```

## Como o LIMIT e exigido

O validador procura:

```text
LIMIT <numero>
```

Se nao encontrar `LIMIT`, a query falha:

```text
A query deve conter LIMIT.
```

Exemplo bloqueado:

```cypher
MATCH (p:Part)
RETURN p.part_id
```

Exemplo aceito:

```cypher
MATCH (p:Part)
RETURN p.part_id
LIMIT 50
```

Se a query vier com limite maior que o permitido pelo CLI, o validador reduz:

```text
LIMIT 500
```

vira:

```text
LIMIT 50
```

e adiciona um aviso:

```text
LIMIT 500 reduzido para 50.
```

## Como o schema conhecido da ontologia e exigido

A validacao exige que a query use pelo menos um label ou relacionamento tipado
da ontologia.

Query bloqueada:

```cypher
MATCH (n)
RETURN n
LIMIT 50
```

Motivo:

```text
A query deve usar pelo menos um label ou relacionamento da ontologia.
```

Isso evita uma varredura generica do grafo inteiro.

Query aceita:

```cypher
MATCH (p:Part)
RETURN p.part_id, p.part_name
LIMIT 50
```

Porque `Part` e um label conhecido.

## Outras protecoes simples

O validador tambem bloqueia:

```text
;
comentarios //
comentarios /* */
identificadores com crase
alternancia com |
```

Essas restricoes reduzem formas simples de esconder ou combinar comandos.

Exemplo bloqueado:

```cypher
MATCH (p:`Part`)
RETURN p
LIMIT 50
```

Motivo:

```text
Identificadores com crase nao sao permitidos.
```

## O que acontece quando passa

Quando a query passa, `require_valid_cypher` retorna um `ValidationResult` com:

```python
validation.cypher
validation.is_valid
validation.errors
validation.warnings
```

O monolito imprime a query validada:

```python
print(validation.cypher)
print(format_validation(validation))
```

Depois executa:

```python
super().query(validation.cypher, ...)
```

Nesse momento a query finalmente chega ao Neo4j.

## Exemplo do fluxo de estoque

Pergunta:

```text
quais pecas estao abaixo do estoque minimo?
```

Cypher esperado:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
WHERE stock.stock_on_hand < stock.min_stock
RETURN
  p.part_id AS part_id,
  p.part_name AS part_name,
  p.criticality AS criticality,
  w.warehouse AS warehouse,
  stock.stock_on_hand AS stock_on_hand,
  stock.min_stock AS min_stock,
  stock.reorder_point AS reorder_point
ORDER BY stock.stock_on_hand ASC, part_id
LIMIT 50
```

Por que passa:

- `Part` e `Warehouse` sao labels conhecidos;
- `STOCKED_AT` e relacionamento conhecido;
- `stock_on_hand`, `min_stock` e `reorder_point` pertencem a `STOCKED_AT`;
- a query comeca com `MATCH`;
- a query tem `RETURN`;
- a query tem `LIMIT 50`;
- nao ha comandos de escrita.

## Papel do usuario read-only

A validacao de aplicacao e uma barreira importante, mas nao deve ser a unica.

Na versao LangChain, o monolito usa:

```python
get_neo4j_read_settings()
```

Essa funcao tenta usar:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

Se essas variaveis existirem, o LangChain consulta o banco com usuario
read-only.

Essa e a defesa final: mesmo que algum caso escape do validador, o banco deve
negar escrita.

## Resumo

Na versao LangChain, o processo de validacao antes do banco funciona assim:

```text
GraphCypherQAChain gera Cypher
  |
  v
ValidatedNeo4jGraph.query intercepta
  |
  v
require_valid_cypher valida
  |
  +--> bloqueia se houver risco
  |
  +--> executa no Neo4j se estiver OK
```

O LangChain acelera o Text2Cypher, mas quem aplica os guardrails do projeto e o
validador local.
