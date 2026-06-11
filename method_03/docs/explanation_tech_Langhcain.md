# Explicacao tecnica: pipeline LangChain

Este documento explica a versao do monolito que roda com:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset
```

Como `--engine langchain` e o padrao, esse comando usa:

```python
langchain_neo4j.GraphCypherQAChain
```

A ideia desta versao e mostrar como usar o framework pronto do LangChain para
Text2Cypher, mas ainda mantendo uma barreira propria de validacao antes do
Neo4j.

## Visao geral do pipeline

```text
Usuario pergunta
  |
  v
monolith.py
  |
  v
CSV -> build_graph() -> Neo4j
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
validator.py
  |
  +--> bloqueia se falhar
  |
  +--> executa no Neo4j se passar
  |
  v
GraphCypherQAChain gera resposta final
```

## O que o LangChain faz

O LangChain entra na etapa de pergunta e resposta.

No monolito, o trecho principal e:

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

Essa chain faz:

- recebe a pergunta do usuario;
- recebe o schema do Neo4j;
- recebe exemplos few-shot;
- pede para a LLM gerar Cypher;
- executa a query usando `graph.query(...)`;
- usa o resultado para gerar a resposta final.

O ponto critico e que o LangChain normalmente executaria a query direto em
`Neo4jGraph.query`. O projeto muda esse comportamento usando um wrapper.

## Por que existe allow_dangerous_requests=True

`GraphCypherQAChain` exige:

```python
allow_dangerous_requests=True
```

Isso nao significa que queremos executar queries perigosas. Significa que o
LangChain exige uma confirmacao explicita de que o desenvolvedor entende o risco
de deixar uma LLM gerar Cypher.

Por isso, a protecao real do projeto nao e essa flag. A protecao real e:

```text
ValidatedNeo4jGraph.query()
validator.py
usuario Neo4j read-only
```

## Como o schema e limitado antes da geracao

O monolito passa:

```python
include_types=sorted(allowed_labels() | allowed_relationships())
```

`allowed_labels()` vem de `schema.py` e retorna os labels da ontologia:

```text
WorkOrder
Asset
AssetClass
Failure
Part
Supplier
Warehouse
```

`allowed_relationships()` retorna:

```text
FOR_ASSET
HAS_FAILURE
HAS_CLASS
COMPATIBLE_WITH
SUPPLIES
STOCKED_AT
CANDIDATE_PART
```

Esse filtro reduz o schema que a LLM ve. Ele ajuda a orientar a geracao, mas nao
e suficiente como validacao de seguranca. Uma LLM ainda pode gerar algo fora do
schema. Por isso a validacao ocorre depois da geracao.

## Prompt usado para gerar Cypher

O monolito cria um prompt proprio para a chain:

```python
cypher_prompt = PromptTemplate(
    input_variables=["schema", "question", "examples"],
    template=_langchain_cypher_prompt(max_rows),
)
```

Esse prompt instrui:

- usar apenas tipos e propriedades do schema;
- usar somente leitura;
- nao usar comandos de escrita;
- incluir `LIMIT`;
- tratar estoque como propriedade da relacao `STOCKED_AT`;
- responder apenas com Cypher, sem explicacao.

Isso e uma primeira barreira, mas ainda e prompt. Prompt nao e garantia.

## Onde a query e interceptada

O monolito cria uma classe dentro de `_run_langchain_graph_cypher_chain`:

```python
class ValidatedNeo4jGraph(Neo4jGraph):
    def query(self, query, params={}, session_params={}):
        validation = require_valid_cypher(query, max_rows=max_rows)
        return super().query(validation.cypher, params=params, session_params=session_params)
```

Essa e a parte mais importante.

O `GraphCypherQAChain` chama:

```python
graph.query(cypher_gerado)
```

Mas `graph` nao e um `Neo4jGraph` puro. Ele e um `ValidatedNeo4jGraph`.

Entao a query nao chega direto no banco. Ela passa por:

```python
require_valid_cypher(...)
```

## Etapas da validacao local

A funcao `require_valid_cypher` chama:

```python
validate_cypher(...)
```

Ela retorna um `ValidationResult` com:

```python
cypher
is_valid
errors
warnings
```

Se `is_valid` for falso, ela levanta `CypherValidationError` e a execucao para.

O banco so recebe a query quando a validacao passa.

## Bloqueio de comandos perigosos

O validador transforma a query em maiusculas para procurar palavras proibidas.

Palavras bloqueadas:

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

Tambem bloqueia frases:

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

## Exigencia de MATCH e RETURN

A query precisa comecar com:

```text
MATCH
```

ou:

```text
OPTIONAL MATCH
```

Tambem precisa conter:

```text
RETURN
```

Isso reduz o espaco de query para leitura simples.

Exemplo bloqueado:

```cypher
WITH 1 AS x
RETURN x
LIMIT 50
```

Mesmo sendo leitura, a regra atual bloqueia porque a query nao comeca com
`MATCH` ou `OPTIONAL MATCH`. Essa decisao deixa a v1 mais restrita e mais facil
de auditar.

## Exigencia de LIMIT

O validador procura:

```text
LIMIT <numero>
```

Sem `LIMIT`, a query e bloqueada.

Exemplo bloqueado:

```cypher
MATCH (p:Part)
RETURN p.part_id
```

Motivo:

```text
A query deve conter LIMIT.
```

Se o limite for maior que `--max-rows`, o validador reduz.

Exemplo:

```cypher
LIMIT 500
```

com `--max-rows 50` vira:

```cypher
LIMIT 50
```

Nesse caso a query ainda pode passar, mas gera um warning.

## Conferencia de labels

O validador procura labels com esta regex:

```python
NODE_PATTERN
```

Ela detecta trechos como:

```cypher
(p:Part)
(wo:WorkOrder)
(w:Warehouse)
```

Cada label e comparado com:

```python
allowed_labels()
```

Se a LLM gerar:

```cypher
MATCH (x:Customer)
RETURN x
LIMIT 50
```

o erro sera:

```text
Label fora da ontologia: Customer.
```

## Conferencia de relacionamentos

O validador procura relacionamentos com:

```python
REL_PATTERN
```

Ele detecta:

```cypher
[stock:STOCKED_AT]
[:FOR_ASSET]
[:HAS_FAILURE]
```

Cada tipo e comparado com:

```python
allowed_relationships()
```

Se a LLM gerar:

```cypher
MATCH (a:Asset)-[:OWNS]->(p:Part)
RETURN a, p
LIMIT 50
```

o erro sera:

```text
Relacionamento fora da ontologia: OWNS.
```

## Conferencia de propriedades

O validador detecta propriedades com:

```python
PROPERTY_PATTERN
```

Ele procura:

```text
alias.propriedade
```

Exemplo:

```cypher
p.part_id
stock.stock_on_hand
w.warehouse
```

Para saber se a propriedade e valida, o validador primeiro mapeia aliases:

```cypher
(p:Part)
[stock:STOCKED_AT]
(w:Warehouse)
```

Depois confere:

- propriedades de node em `NODE_PROPERTIES`;
- propriedades de relacionamento em `RELATIONSHIP_PROPERTIES`.

Exemplo correto:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
RETURN p.part_id, stock.stock_on_hand, w.warehouse
LIMIT 50
```

Exemplo bloqueado:

```cypher
MATCH (p:Part)-[:STOCKED_AT]->(w:Warehouse)
RETURN w.stock_on_hand
LIMIT 50
```

Motivo: `stock_on_hand` pertence a relacao `STOCKED_AT`, nao ao label
`Warehouse`.

## Bloqueios contra atalhos e bypass simples

O validador tambem bloqueia:

```text
;
comentarios //
comentarios /* */
crases `
alternancia |
```

Essas regras evitam:

- multiplas statements;
- esconder comandos em comentarios;
- usar identificadores escapados para contornar regex simples;
- alternar labels ou relacionamentos no mesmo padrao.

## Exigencia de ontologia conhecida

Se a query nao tiver nenhum label ou relacionamento tipado, ela e bloqueada.

Exemplo:

```cypher
MATCH (n)
RETURN n
LIMIT 50
```

Motivo:

```text
A query deve usar pelo menos um label ou relacionamento da ontologia.
```

Isso evita um full graph scan generico.

## O que acontece quando falha

Quando a query falha:

```python
require_valid_cypher(...)
```

levanta:

```python
CypherValidationError
```

O `main` captura essa excecao:

```python
except CypherValidationError as exc:
    print("Cypher bloqueado pelo validador:", file=sys.stderr)
    print(format_validation(exc.result), file=sys.stderr)
    return 1
```

Resultado: a query nao executa no Neo4j.

## O que acontece quando passa

Quando a query passa:

```python
return super().query(validation.cypher, ...)
```

Nesse momento o `ValidatedNeo4jGraph` chama o `Neo4jGraph.query` original do
LangChain, mas usando a versao validada da query.

Depois disso, o `GraphCypherQAChain` recebe as linhas retornadas e gera a
resposta final.

## Papel do usuario read-only

Mesmo com validador, a protecao mais forte deve estar no banco.

A versao LangChain usa:

```python
get_neo4j_read_settings()
```

Isso permite configurar:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

Em producao, esse usuario deve ter permissao somente leitura.

Assim, mesmo que uma query perigosa escape, o Neo4j nao deve permitir alteracao.

## Resumo tecnico

Na engine LangChain:

```text
GraphCypherQAChain gera e orquestra.
ValidatedNeo4jGraph intercepta.
validator.py decide.
Neo4j executa apenas se passar.
GraphCypherQAChain responde.
```

Essa abordagem aproveita o framework pronto, mas preserva uma validacao local
explicita antes do banco.
