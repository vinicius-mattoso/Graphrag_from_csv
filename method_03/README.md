# Metodo 03: GraphRAG com Text2Cypher

O Metodo 03 e a evolucao natural do Metodo 02.

No Metodo 02, a recuperacao usa Cypher controlado e predefinido. A LLM nao
escreve consultas Cypher; ela apenas recebe o contexto recuperado do Neo4j e
gera a resposta final.

No Metodo 03, a proposta e permitir que a LLM gere consultas Cypher a partir da
pergunta do usuario, usando um processo Text2Cypher. Essa geracao, no entanto,
nao deve ser livre. A query precisa passar por validacao antes de ser executada.

```text
Pergunta do usuario
    |
    v
Schema do grafo + exemplos few-shot
    |
    v
LLM gera Cypher somente leitura
    |
    v
Validador bloqueia query perigosa ou fora da ontologia
    |
    v
Neo4j executa com usuario read-only
    |
    v
Resultados estruturados
    |
    v
LLM gera resposta final com evidencias
```

## Diferenca para o Metodo 02

| Metodo | Como recupera contexto | Papel da LLM na query |
| --- | --- | --- |
| `method_02` | Vector search + Cypher fixo/controlado | A LLM nao cria Cypher |
| `method_03` | Text2Cypher validado + Neo4j | A LLM propoe Cypher, mas nao executa diretamente |

O Metodo 03 nao substitui a ingestao do Metodo 02. Ele deve consultar o mesmo
grafo Neo4j ja carregado com nos, arestas, documentos e embeddings.

## Por que usar Text2Cypher?

Cypher fixo funciona bem quando as perguntas seguem um padrao conhecido, como:

```text
quais pecas podem ajudar em queda de pressao no compressor?
```

Mas ele fica limitado quando o usuario faz perguntas mais variadas, por exemplo:

```text
quais pecas estao abaixo do estoque minimo?
quais fornecedores atendem pecas criticas?
quais falhas aparecem em bombas centrifugas?
quais ordens tiveram maior downtime?
```

Nesses casos, o Text2Cypher permite gerar uma consulta mais especifica para a
pergunta.

## Schema enviado para a LLM

A LLM deve receber uma descricao controlada do grafo, baseada na ontologia do
projeto.

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
(:WorkOrder)-[:FOR_ASSET]->(:Asset)
(:WorkOrder)-[:HAS_FAILURE]->(:Failure)
(:Asset)-[:HAS_CLASS]->(:AssetClass)
(:Part)-[:COMPATIBLE_WITH]->(:AssetClass)
(:Supplier)-[:SUPPLIES]->(:Part)
(:Part)-[:STOCKED_AT]->(:Warehouse)
(:WorkOrder)-[:CANDIDATE_PART]->(:Part)
```

A LLM tambem deve receber exemplos de pergunta e Cypher esperado.

## Exemplo de Text2Cypher

Pergunta:

```text
quais pecas estao abaixo do estoque minimo?
```

Cypher esperado:

```cypher
MATCH (p:Part)-[:STOCKED_AT]->(w:Warehouse)
WHERE w.stock_on_hand < w.min_stock
RETURN
  p.part_id AS part_id,
  p.part_name AS part_name,
  w.warehouse AS warehouse,
  w.stock_on_hand AS stock_on_hand,
  w.min_stock AS min_stock,
  w.reorder_point AS reorder_point
ORDER BY w.stock_on_hand ASC, part_id
LIMIT 50
```

Resposta esperada:

```text
As pecas abaixo do estoque minimo sao ...
```

## Validacao obrigatoria

A LLM nunca deve executar Cypher diretamente.

Ela apenas propoe uma query. A aplicacao valida a query antes de executar.

A validacao deve bloquear comandos que alterem o banco:

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
CREATE INDEX
CREATE CONSTRAINT
DROP INDEX
DROP CONSTRAINT
```

Tambem deve bloquear:

```text
;
multiplas statements
labels fora da ontologia
relacionamentos fora da ontologia
propriedades inexistentes
queries sem LIMIT
```

O conjunto permitido deve ser restrito a leitura:

```text
MATCH
OPTIONAL MATCH
WHERE
WITH
RETURN
ORDER BY
LIMIT
SKIP
```

## Usuario Neo4j read-only

A validacao na aplicacao e necessaria, mas nao e suficiente.

O Metodo 03 tambem deve usar um usuario Neo4j com permissao somente leitura.
Assim, mesmo que uma query perigosa passe por erro de validacao, o banco ainda
bloqueia alteracoes.

Regra pratica:

```text
A LLM pode propor.
A aplicacao valida.
O banco protege.
```

## Fluxo recomendado

1. Receber pergunta do usuario.
2. Montar prompt com schema, regras e exemplos.
3. Pedir para a LLM retornar JSON com `cypher`, `parameters` e resumo curto.
4. Validar a query.
5. Rodar `EXPLAIN` no Neo4j para checar sintaxe.
6. Executar a query validada com limite de linhas.
7. Enviar resultados para a LLM gerar a resposta final.
8. Mostrar, opcionalmente, a query gerada para auditoria.

## Interface sugerida

```powershell
python -m method_03.script_ask "quais pecas estao abaixo do estoque minimo?" --show-cypher
```

Flags uteis:

```text
--show-cypher   Mostra a query gerada.
--show-context  Mostra os resultados retornados pelo Neo4j.
--dry-run       Gera e valida a query, mas nao executa.
--max-rows 50   Limita a quantidade de linhas retornadas.
```

## Limites da abordagem

Text2Cypher aumenta flexibilidade, mas tambem aumenta risco.

Principais riscos:

- a LLM pode gerar Cypher sintaticamente errado;
- a LLM pode usar labels ou propriedades que nao existem;
- a LLM pode criar uma consulta ampla demais;
- o resultado pode parecer correto mesmo quando a query recuperou dados ruins;
- prompts maliciosos podem tentar induzir alteracao no banco.

Por isso, o Metodo 03 deve nascer com guardrails fortes, logs de auditoria e
comparacao com o Metodo 02.

## Resumo

O Metodo 03 deve ser visto como uma camada mais inteligente de consulta sobre o
mesmo grafo Neo4j.

A evolucao principal e:

```text
Cypher fixo -> Text2Cypher validado
```

Mas a regra central permanece:

```text
A resposta final so pode usar dados retornados de uma query validada e
executada em modo somente leitura.
```
