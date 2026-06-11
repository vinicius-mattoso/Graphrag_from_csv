# Explicacao: monolito LangChain puro

Este documento explica o arquivo:

```text
method_03/monolith_langchain_raw.py
```

Essa versao existe para estudar as capacidades nativas do LangChain com Neo4j,
principalmente:

```python
Neo4jGraph
GraphCypherQAChain
```

Diferente do `method_03.monolith`, esta versao nao usa os guardrails locais do
projeto.

## Objetivo

O objetivo e observar como o framework funciona de ponta a ponta:

```text
pergunta em linguagem natural
  -> schema descoberto pelo LangChain
  -> LLM gera Cypher
  -> LangChain executa no Neo4j
  -> LLM gera resposta final
```

Esse script e util para responder perguntas como:

- como o LangChain descobre o schema?
- como ele transforma linguagem natural em Cypher?
- como ele executa a query?
- como ele mostra os passos intermediarios?
- quais sao as limitacoes quando nao adicionamos validacao propria?

## Como executar

Com ingestao dos CSVs antes da pergunta:

```powershell
python -m method_03.monolith_langchain_raw "quais pecas estao abaixo do estoque minimo?" --reset
```

Usando um grafo que ja esta no Neo4j:

```powershell
python -m method_03.monolith_langchain_raw "quais pecas estao abaixo do estoque minimo?" --skip-ingestion
```

Desligando tambem o corretor Cypher nativo do LangChain:

```powershell
python -m method_03.monolith_langchain_raw "quais pecas estao abaixo do estoque minimo?" --skip-ingestion --no-validate-cypher
```

## Fluxo do script

O script imprime etapas numeradas:

```text
1. Validando ambiente
2. Lendo CSVs e gravando grafo no Neo4j
3. Criando Neo4jGraph puro do LangChain
4. Criando GraphCypherQAChain puro
5. Executando pergunta sem validador local
```

Essas etapas mostram o caminho completo sem esconder a preparacao do grafo.

## Etapa 1: validar ambiente

O script chama:

```python
require_method_03_llm_runtime()
```

Isso exige:

```text
OPENAI_API_KEY
```

Depois carrega duas configuracoes:

```python
write_settings = get_neo4j_settings()
read_settings = get_neo4j_read_settings()
```

`write_settings` e usado para ingerir dados no Neo4j.

`read_settings` e usado pelo `Neo4jGraph` do LangChain para consultar o banco.

Se existirem:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

elas sao usadas na consulta. Caso contrario, o script usa as credenciais normais:

```text
NEO4J_USERNAME
NEO4J_PASSWORD
```

## Etapa 2: ingerir os CSVs

Se voce nao usar `--skip-ingestion`, o script executa:

```python
graph = build_graph()
stats = ingest_graph_to_neo4j(graph, settings=write_settings, reset=args.reset)
```

Isso reaproveita a construcao de grafo do `method_01` e grava no Neo4j:

- labels de dominio, como `Part`, `Warehouse`, `Failure`, `WorkOrder`;
- relacionamentos, como `STOCKED_AT`, `SUPPLIES`, `HAS_FAILURE`;
- propriedades vindas dos CSVs.

Essa etapa nao e parte do Text2Cypher em si. Ela apenas garante que existe um
grafo para consultar.

## Etapa 3: criar Neo4jGraph

O script cria:

```python
Neo4jGraph(
    url=settings.uri,
    username=settings.username,
    password=settings.password,
    database=settings.database,
    refresh_schema=True,
)
```

O ponto importante e:

```python
refresh_schema=True
```

Com isso, o LangChain consulta o Neo4j para descobrir o schema do grafo.

Depois o script imprime:

```python
graph_store.schema
```

Esse schema e o principal contexto usado pela LLM para gerar Cypher.

## O que existe no schema do LangChain

O `Neo4jGraph` tenta montar uma representacao textual com:

- labels;
- propriedades de nodes;
- tipos de relacionamento;
- propriedades de relacionamentos;
- padroes de conexao entre labels.

Exemplo conceitual:

```text
Node properties:
Part {part_id, part_name, criticality, unit_cost}
Warehouse {warehouse}

Relationship properties:
STOCKED_AT {stock_on_hand, min_stock, reorder_point}

Relationships:
(:Part)-[:STOCKED_AT]->(:Warehouse)
```

Quando a pergunta menciona "pecas abaixo do estoque minimo", a LLM usa esse
schema para inferir que precisa passar por:

```text
Part -> STOCKED_AT -> Warehouse
```

## Etapa 4: criar GraphCypherQAChain

O script cria a chain assim:

```python
GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph_store,
    validate_cypher=validate_cypher,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,
    top_k=top_k,
)
```

Essa e a peca principal do LangChain.

Ela combina duas tarefas:

1. gerar uma query Cypher a partir da pergunta;
2. gerar uma resposta final a partir das linhas retornadas pelo Neo4j.

## Como a pergunta vira Cypher

Quando o usuario pergunta:

```text
quais pecas estao abaixo do estoque minimo?
```

o LangChain monta internamente um prompt com:

```text
Task: Generate Cypher statement to query a graph database.
Use only the provided relationship types and properties in the schema.
Schema:
<schema descoberto no Neo4j>
Question:
quais pecas estao abaixo do estoque minimo?
```

A LLM interpreta termos da pergunta usando o schema:

| Termo da pergunta | Possivel mapeamento no grafo |
| --- | --- |
| `pecas` | label `Part` |
| `estoque` | relacionamento `STOCKED_AT` |
| `estoque minimo` | propriedade `min_stock` |
| `abaixo` | comparacao `<` |
| `almoxarifado` quando aparecer | label `Warehouse` |

Com isso, ela pode gerar uma query parecida com:

```cypher
MATCH (p:Part)-[s:STOCKED_AT]->(w:Warehouse)
WHERE s.stock_on_hand < s.min_stock
RETURN p.part_id, p.part_name, w.warehouse, s.stock_on_hand, s.min_stock
LIMIT 10
```

## validate_cypher do LangChain

O parametro:

```python
validate_cypher=True
```

liga o corretor nativo do LangChain.

Ele e usado principalmente para tentar corrigir ou validar a direcao de
relacionamentos com base no schema.

Exemplo conceitual:

```cypher
(:Warehouse)<-[:STOCKED_AT]-(:Part)
```

versus:

```cypher
(:Part)-[:STOCKED_AT]->(:Warehouse)
```

Esse recurso nao e o mesmo que o `validator.py` do projeto. Ele nao deve ser
tratado como uma politica completa de seguranca.

## O que esta versao nao valida

Esta versao nao usa:

```python
validator.py
ValidatedNeo4jGraph
include_types=...
prompt customizado do projeto
```

Portanto, ela nao aplica os bloqueios locais que existem no monolito principal.

Ela nao confere, pela camada do projeto:

- comandos proibidos;
- labels permitidos pela ontologia do projeto;
- propriedades permitidas por alias;
- obrigatoriedade de `LIMIT`;
- bloqueio de `CALL`, `APOC`, `DELETE`, `SET`, `CREATE`;
- full graph scan sem label.

O objetivo aqui e ver o que o LangChain faz por conta propria.

## allow_dangerous_requests

O `GraphCypherQAChain` exige:

```python
allow_dangerous_requests=True
```

Essa flag existe porque uma chain que gera Cypher pode ser perigosa.

O LangChain obriga o desenvolvedor a declarar explicitamente que entende esse
risco.

Na pratica, isso reforca que este script deve ser usado apenas para estudo ou
com usuario Neo4j read-only.

## top_k

O parametro:

```python
top_k=10
```

controla quantas linhas retornadas pela query sao usadas como contexto pela
chain para gerar a resposta final.

Voce pode ajustar:

```powershell
python -m method_03.monolith_langchain_raw "quais pecas estao abaixo do estoque minimo?" --top-k 20
```

Isso nao e a mesma coisa que obrigar a query a ter `LIMIT 20`. E um limite de
contexto usado pela chain apos a consulta.

## Passos intermediarios

O script usa:

```python
return_intermediate_steps=True
```

Por isso, ao final, ele imprime:

```python
result["intermediate_steps"]
```

Normalmente isso inclui:

- a query Cypher gerada;
- o contexto retornado pelo Neo4j.

Essa e a melhor forma de observar como a pergunta virou Cypher.

## Comparacao com os outros monolitos

| Script | Usa LangChain GraphCypherQAChain | Usa validator.py | Objetivo |
| --- | --- | --- | --- |
| `monolith_langchain_raw.py` | Sim | Nao | Estudar framework puro |
| `monolith.py --engine langchain` | Sim | Sim | Usar framework com guardrails locais |
| `monolith.py --engine custom` | Nao | Sim | Entender pipeline local completo |

## Quando usar esta versao

Use `monolith_langchain_raw.py` para aprender:

- como `Neo4jGraph` descobre schema;
- como `GraphCypherQAChain` monta Text2Cypher;
- qual Cypher a LLM gera so com o schema do banco;
- como a resposta final e formada pelo framework.

Nao use esta versao como referencia de seguranca.

## Risco principal

Sem guardrails locais, a chain pode gerar Cypher inadequado para producao.

Por isso, mesmo nessa versao de estudo, e recomendado configurar usuario Neo4j
somente leitura:

```text
NEO4J_READ_USERNAME
NEO4J_READ_PASSWORD
```

## Resumo

O monolito LangChain puro mostra o framework como ele e:

```text
Neo4jGraph descobre o schema.
GraphCypherQAChain pede Cypher para a LLM.
Neo4jGraph executa a query.
GraphCypherQAChain gera a resposta.
```

Ele e excelente para entender as capacidades nativas do LangChain.

O monolito principal continua sendo melhor para estudar como adicionar controle,
validacao e seguranca em cima desse framework.
