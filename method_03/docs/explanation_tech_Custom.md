# Explicacao tecnica: pipeline custom

Este documento explica a versao do monolito que roda com:

```powershell
python -m method_03.monolith "quais pecas estao abaixo do estoque minimo?" --reset --engine custom
```

Nessa versao, o projeto nao usa `GraphCypherQAChain`. Em vez disso, cada etapa
do pipeline aparece explicitamente nos modulos locais.

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
text2cypher.py gera Cypher em JSON
  |
  v
validator.py valida
  |
  v
neo4j_store.py executa
  |
  v
retrieval.py gera resposta final
```

Essa versao e mais verbosa, mas e a melhor para entender o que acontece em cada
etapa.

## Onde o custom roda no monolito

O `main` escolhe a engine:

```python
if args.engine == "langchain":
    _run_langchain_graph_cypher_chain(...)
else:
    _run_custom_text2cypher(...)
```

Com `--engine custom`, o fluxo entra em:

```python
_run_custom_text2cypher(...)
```

Essa funcao chama quatro etapas:

```python
generate_cypher(...)
require_valid_cypher(...)
run_read_query(...)
generate_answer(...)
```

## Etapa 1: gerar Cypher com text2cypher.py

O modulo `text2cypher.py` monta um prompt com:

- system prompt;
- schema controlado;
- regras obrigatorias;
- exemplos few-shot;
- pergunta do usuario;
- formato de saida esperado.

O system prompt diz:

```text
Voce converte perguntas de manutencao industrial em Cypher somente leitura.
Responda apenas com JSON valido, sem markdown e sem texto extra.
A query deve usar somente o schema fornecido, deve conter RETURN e LIMIT, e nunca pode alterar o banco.
Use parametros no campo "parameters" quando houver valores filtraveis.
```

O human prompt inclui regras como:

```text
Use apenas MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT e SKIP.
Nao use CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, LOAD CSV, CALL, APOC, FOREACH ou USE.
Nao use labels, relacionamentos ou propriedades fora do schema.
Inclua LIMIT menor ou igual a max_rows.
Para estoque, use propriedades da relacao STOCKED_AT.
```

## Saida esperada da LLM

A LLM deve retornar JSON:

```json
{
  "cypher": "MATCH ... RETURN ... LIMIT 50",
  "parameters": {},
  "reasoning_summary": "Resumo curto do caminho usado no grafo"
}
```

Esse JSON e convertido para:

```python
CypherGeneration
```

com:

```python
cypher
parameters
reasoning_summary
raw_response
```

## Parser da resposta da LLM

O metodo:

```python
parse_generation_response(...)
```

tenta carregar o texto como JSON.

Se a LLM devolver markdown com bloco de codigo, o parser remove a cerca:

```text
```json
...
```
```

Se ainda assim o JSON vier misturado com texto, ele tenta extrair do primeiro
`{` ate o ultimo `}`.

Esse parser e simples e didatico. Ele existe para lidar com pequenas variacoes
de saida da LLM.

## Etapa 2: validar com validator.py

Depois de gerar a query, o custom chama:

```python
validation = require_valid_cypher(generation.cypher, max_rows=max_rows)
```

Essa e a principal barreira antes do banco.

Se a query falhar, `require_valid_cypher` levanta `CypherValidationError`.

Se passar, retorna `ValidationResult`.

## Estrutura do ValidationResult

```python
ValidationResult(
    cypher=str,
    is_valid=bool,
    errors=list[str],
    warnings=list[str],
)
```

O campo `cypher` pode ser diferente da query original se o validador reduzir o
`LIMIT`.

## Normalizacao inicial

O validador comeca chamando:

```python
_normalize_cypher(...)
```

Ele remove espacos desnecessarios no fim das linhas e tira espacos no comeco e
no fim do texto.

Depois cria:

```python
upper = normalized.upper()
```

Essa versao em maiusculas facilita encontrar comandos proibidos.

## Bloqueio de multiplas statements

Se houver:

```text
;
```

a query falha.

Motivo: ponto e virgula pode indicar multiplas statements ou tentativa de
encaixar outra operacao depois da query principal.

Exemplo bloqueado:

```cypher
MATCH (p:Part) RETURN p LIMIT 10; MATCH (n) DELETE n
```

## Bloqueio de comentarios, crases e alternancia

O validador bloqueia:

```text
//
/*
*/
`
|
```

Motivos:

- comentarios podem esconder trechos perigosos;
- crases podem escapar identificadores e dificultar regex;
- `|` permite alternancia de labels ou relacionamentos;
- o objetivo da v1 e manter a sintaxe simples e auditavel.

## Bloqueio de comandos perigosos

O validador usa duas listas:

```python
FORBIDDEN_PHRASES
FORBIDDEN_WORDS
```

Frases proibidas:

```text
CREATE INDEX
CREATE CONSTRAINT
DROP INDEX
DROP CONSTRAINT
LOAD CSV
```

Palavras proibidas:

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

Tambem bloqueia algumas leituras avancadas na v1:

```text
UNWIND
UNION
PROFILE
EXPLAIN
SHOW
YIELD
```

Isso deixa o espaco permitido mais estreito.

## Exigencia de inicio seguro

A query deve comecar com:

```text
MATCH
```

ou:

```text
OPTIONAL MATCH
```

Essa regra e mais restritiva que Cypher completo. Ela simplifica a validacao e
evita que a LLM comece com construcoes menos esperadas.

## Exigencia de RETURN

O validador procura a palavra:

```text
RETURN
```

Sem `RETURN`, nao ha resultado para responder.

Exemplo bloqueado:

```cypher
MATCH (p:Part)
LIMIT 50
```

## Exigencia e ajuste de LIMIT

O validador procura:

```python
LIMIT_PATTERN
```

que reconhece:

```text
LIMIT <numero>
```

Se nao houver `LIMIT`, a query falha.

Se houver `LIMIT` maior que `max_rows`, o validador troca pelo maximo permitido.

Exemplo:

```cypher
MATCH (p:Part)
RETURN p.part_id
LIMIT 500
```

com `max_rows=50` vira:

```cypher
MATCH (p:Part)
RETURN p.part_id
LIMIT 50
```

e gera warning.

## Conferencia de labels

O validador usa:

```python
NODE_PATTERN
```

para encontrar aliases e labels:

```cypher
(p:Part)
(wo:WorkOrder)
(asset:Asset)
```

Ele monta um mapa:

```python
node_aliases = {"p": "Part", "wo": "WorkOrder"}
```

Depois confere se cada label esta em:

```python
allowed_labels()
```

Se nao estiver, bloqueia.

## Conferencia de relacionamentos

O validador usa:

```python
REL_PATTERN
```

para encontrar relacionamentos:

```cypher
[stock:STOCKED_AT]
[supply:SUPPLIES]
[:HAS_FAILURE]
```

Ele confere cada tipo em:

```python
allowed_relationships()
```

Se estiver fora da ontologia, bloqueia.

## Conferencia de propriedades

O validador usa:

```python
PROPERTY_PATTERN
```

para encontrar:

```text
alias.propriedade
```

Depois olha o alias.

Se o alias for de node:

```python
properties_for_label(label)
```

Se o alias for de relacionamento:

```python
properties_for_relationship(relationship_type)
```

Exemplo correto:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
RETURN p.part_id, stock.stock_on_hand, w.warehouse
LIMIT 50
```

Exemplo bloqueado:

```cypher
MATCH (p:Part)-[stock:STOCKED_AT]->(w:Warehouse)
RETURN p.stock_on_hand
LIMIT 50
```

Motivo: `stock_on_hand` pertence ao relacionamento `STOCKED_AT`, nao a `Part`.

## Exigencia de ontologia tipada

Se a query nao tiver nenhum label ou relacionamento tipado, ela falha.

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

Isso evita uma consulta generica no grafo inteiro.

## Etapa 3: executar com neo4j_store.py

Depois da validacao, o custom chama:

```python
rows = run_read_query(validation.cypher, generation.parameters, settings=settings)
```

Essa funcao:

1. abre driver Neo4j;
2. abre uma session no database configurado;
3. roda `EXPLAIN` para validar sintaxe no Neo4j;
4. executa a query;
5. retorna `data()` como lista de dicionarios.

O `EXPLAIN` nao executa a query, mas checa se o Neo4j entende a sintaxe e o
plano.

## Etapa 4: gerar resposta com retrieval.py

Com as linhas retornadas, o custom chama:

```python
generate_answer(...)
```

O prompt da resposta recebe:

- pergunta original;
- resumo do caminho Text2Cypher;
- Cypher validado;
- parametros;
- resultados do Neo4j.

O system prompt orienta a LLM a responder usando apenas os resultados do Neo4j.

## Exemplo completo de estoque

Pergunta:

```text
quais pecas estao abaixo do estoque minimo?
```

Cypher gerado:

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

Linhas retornadas:

```text
P-006 | estoque 0 | minimo 2
P-003 | estoque 1 | minimo 3
P-001 | estoque 3 | minimo 5
```

Resposta final:

```text
As pecas abaixo do estoque minimo sao P-006, P-003 e P-001...
```

## Diferenca para a engine LangChain

Na engine LangChain, a chain esconde parte do fluxo:

```text
gera Cypher -> consulta -> responde
```

Na engine custom, o projeto controla tudo explicitamente:

```text
gera Cypher -> valida -> EXPLAIN -> executa -> responde
```

Por isso a engine custom e melhor para estudar a arquitetura e para evoluir
guardrails proprios.

## Resumo tecnico

Na engine custom:

```text
text2cypher.py cria a proposta.
validator.py decide se a proposta e segura.
neo4j_store.py executa se passar.
retrieval.py gera a resposta final.
```

A validacao e uma etapa explicita e obrigatoria entre a LLM e o banco.
